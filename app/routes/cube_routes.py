from flask import Blueprint, request, jsonify, current_app
from pydantic import ValidationError
from app.models import CubeFace
from app.utils import request_timeout_handler
from app.errors import ClientDisconnectError
from app.services.rubiks_cv_analyzer import analyze_cube_hybrid
from app.inference import call_vision_inference_streaming

cube_bp = Blueprint('cube', __name__)

@cube_bp.route('/analyze-cube', methods=['POST'])
def analyze_cube():
    try:
        with request_timeout_handler() as check_connection:
            if 'image' not in request.files:
                return jsonify({"error": "No image provided"}), 400
            image = request.files['image']
            if image.filename == '':
                return jsonify({"error": "Empty filename"}), 400

            image_data = image.read()
            check_connection()

            def llm_fallback(img_data, chk_conn):
                service_url = current_app.config['CUBE_ANALYSIS_INFERENCE_SERVICE_URL']
                service_type = current_app.config['SERVICE_TYPE']
                model = current_app.config['CUBE_ANALYSIS_MODEL']
                return call_vision_inference_streaming(img_data, chk_conn, service_url, model, service_type)

            try:
                # Use the hybrid analysis function with the LLM fallback
                result = analyze_cube_hybrid(image_data, check_connection, llm_fallback_func=llm_fallback)
                if not result:
                    return jsonify({"error": "Failed to analyze cube with both CV and LLM"}), 500

                cube_face = CubeFace(**result)
            except ValidationError as e:
                return jsonify({"error": "Invalid inference response", "details": e.errors()}), 422

            return jsonify({"success": True, "cube_face": cube_face.model_dump()}), 200

    except ClientDisconnectError:
        current_app.logger.info("Client disconnected during inference")
        return '', 499
    except Exception as e:
        return jsonify({"error": "Unexpected error", "details": str(e)}), 500

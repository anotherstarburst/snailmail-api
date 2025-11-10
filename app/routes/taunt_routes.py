
from flask import Blueprint, request, jsonify, current_app
from pydantic import ValidationError
from app.models import TauntRequest, TauntResponse
from app.inference import call_text_inference

taunt_bp = Blueprint('taunt', __name__)

@taunt_bp.route('/taunt', methods=['POST'])
def generate_taunt():
    try:
        data = request.get_json()
        taunt_request = TauntRequest(**data)
        app_cfg = current_app.config
        service_type = app_cfg['SERVICE_TYPE']
        service_url = app_cfg['WITTY_TEXT_INFERENCE_SERVICE_URL']
        model = app_cfg['WITTY_TEXT_MODEL']

        prompt = (
            f"You are the character '{taunt_request.npc_character}'. "
            f"Generate some short, witty trash talk directed at your opponent, '{taunt_request.player_character}'. "
            # f"Context: {taunt_request.context or ''}. "
            "Your response must be a single JSON object with one key: 'taunt'. "
            "Example: {\"taunt\": \"You cross my mind only on Thursday morning, that's when I take out the garbage.\"}"
        )

        result = call_text_inference(prompt, service_url, model, service_type)

        if result is None:
            return jsonify({
                "error": "Failed to get a valid response from the inference service."
            }), 503

        taunt_response = TauntResponse(**result)

        return jsonify({
            "success": True,
            "taunt": taunt_response.taunt,
            "npc_character": taunt_request.npc_character,
            "player_character": taunt_request.player_character
        }), 200

    except ValidationError as e:
        return jsonify({"error": "Invalid request", "details": e.errors()}), 400
    except Exception as e:
        current_app.logger.error(f"Unexpected error in /taunt: {str(e)}")
        return jsonify({"error": "Unexpected error", "details": str(e)}), 500

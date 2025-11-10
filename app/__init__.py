import os
from flask import Flask, jsonify
from flask_cors import CORS
from dotenv import load_dotenv
import logging

load_dotenv()

def create_app():
    app = Flask(__name__)
    logging.basicConfig(level=logging.INFO)

    # Configuration
    app.config['SERVICE_TYPE'] = os.getenv('SERVICE_TYPE', 'ollama')
    app.config['WITTY_TEXT_INFERENCE_SERVICE_URL'] = os.getenv('WITTY_TEXT_INFERENCE_SERVICE_URL', 'http://localhost:11434')
    app.config['CUBE_ANALYSIS_INFERENCE_SERVICE_URL'] = os.getenv('CUBE_ANALYSIS_INFERENCE_SERVICE_URL', 'http://localhost:11434')
    app.config['CORS_ORIGINS'] = os.getenv('CORS_ORIGINS', '*')
    app.config['PORT'] = int(os.getenv('PORT', 5000))
    app.config['DEBUG'] = os.getenv('DEBUG', 'False').lower() == 'true'
    app.config['WITTY_TEXT_MODEL'] = os.getenv('WITTY_TEXT_MODEL', 'gemma3:1b')
    app.config['CUBE_ANALYSIS_MODEL'] = os.getenv('CUBE_ANALYSIS_MODEL', 'gemma3:12b')

    # CORS setup
    cors_origins = app.config['CORS_ORIGINS']
    cors_origins = cors_origins if cors_origins == '*' else [o.strip() for o in cors_origins.split(',')]
    CORS(app, resources={r"/*": {"origins": cors_origins, "methods": ["GET", "POST", "OPTIONS"], "allow_headers": ["Content-Type"]}})

    # Register routes
    from app.routes.cube_routes import cube_bp
    from app.routes.taunt_routes import taunt_bp
    app.register_blueprint(cube_bp)
    app.register_blueprint(taunt_bp)

    @app.route('/health')
    def health():
        keys = [
            "SERVICE_TYPE",
            # "WITTY_TEXT_INFERENCE_SERVICE_URL",
            # "CUBE_ANALYSIS_INFERENCE_SERVICE_URL",
            "CORS_ORIGINS",
            # "PORT",
            # "DEBUG",
            "WITTY_TEXT_MODEL",
            "CUBE_ANALYSIS_MODEL"
        ]
        env_vars = {key: os.getenv(key) for key in keys}
        return jsonify(env_vars)

    return app

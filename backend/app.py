"""
ValueTrack — Flask Application Entry Point
Registers blueprints, CORS, session teardown, and health check.
"""
from flask import Flask, jsonify
from flask_cors import CORS
from config import Config
from db import db_session, shutdown_session, init_db


def create_app():
    """Application factory."""
    app = Flask(__name__)
    app.config.from_object(Config)
    app.config['MAX_CONTENT_LENGTH'] = Config.MAX_CONTENT_LENGTH

    # CORS — allow frontend on different ports during development
    CORS(app, supports_credentials=True, origins=['http://localhost:8000', 'http://127.0.0.1:8000',
                                                   'http://localhost:5500', 'http://127.0.0.1:5500',
                                                   'null'])

    # Teardown: remove DB session after each request
    app.teardown_appcontext(shutdown_session)

    # ---- Register Blueprints ----
    from routes.auth_routes import auth_bp
    from routes.loan_routes import loan_bp
    from routes.expense_routes import expense_bp
    from routes.insurance_routes import insurance_bp
    from routes.dashboard_routes import dashboard_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(loan_bp)
    app.register_blueprint(expense_bp)
    app.register_blueprint(insurance_bp)
    app.register_blueprint(dashboard_bp)

    # ---- Health Check ----
    @app.route('/api/health', methods=['GET'])
    def health():
        return jsonify({'status': 'ok', 'service': 'ValueTrack API'}), 200

    # ---- Error Handlers ----
    @app.errorhandler(413)
    def request_entity_too_large(error):
        return jsonify({'error': 'File too large. Maximum size is 10MB.'}), 413

    @app.errorhandler(404)
    def not_found(error):
        return jsonify({'error': 'Resource not found'}), 404

    @app.errorhandler(500)
    def internal_error(error):
        return jsonify({'error': 'Internal server error'}), 500

    return app


if __name__ == '__main__':
    app = create_app()
    print("=" * 50)
    print("  ValueTrack API Server")
    print("  Running on http://127.0.0.1:5000")
    print("=" * 50)
    app.run(host='127.0.0.1', port=5000, debug=Config.DEBUG)

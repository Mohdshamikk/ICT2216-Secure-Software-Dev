from flask import Flask, jsonify
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from app.config import config
from app.extensions import db, cors

limiter = Limiter(key_func=get_remote_address, default_limits=[])


def create_app(config_name='development'):
    app = Flask(__name__)
    app.config.from_object(config[config_name])

    db.init_app(app)
    cors.init_app(app, origins=app.config['FRONTEND_URL'])
    limiter.init_app(app)

    from app.routes.health import health_bp
    from app.routes.auth import auth_bp
    from app.routes.users import users_bp
    from app.routes.statements import statements_bp
    from app.routes.transactions import transactions_bp
    from app.routes.consents import consents_bp
    from app.routes.admin import admin_bp

    app.register_blueprint(health_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(users_bp)
    app.register_blueprint(statements_bp)
    app.register_blueprint(transactions_bp)
    app.register_blueprint(consents_bp)
    app.register_blueprint(admin_bp)

    @app.errorhandler(400)
    def bad_request(e):
        return jsonify(error='Bad request'), 400

    @app.errorhandler(401)
    def unauthorised(e):
        return jsonify(error='Unauthorised'), 401

    @app.errorhandler(403)
    def forbidden(e):
        return jsonify(error='Forbidden'), 403

    @app.errorhandler(404)
    def not_found(e):
        return jsonify(error='Not found'), 404

    @app.errorhandler(405)
    def method_not_allowed(e):
        return jsonify(error='Method not allowed'), 405

    @app.errorhandler(413)
    def payload_too_large(e):
        return jsonify(error='File too large'), 413

    @app.errorhandler(415)
    def unsupported_media(e):
        return jsonify(error='Unsupported file type'), 415

    @app.errorhandler(429)
    def too_many_requests(e):
        return jsonify(error='Too many requests'), 429

    @app.errorhandler(500)
    def internal_error(e):
        return jsonify(error='Internal server error'), 500

    return app
from flask import Flask, jsonify
from app.database_engine import SessionLocal

# from .config import Config

def create_app() -> Flask:
    app = Flask(__name__)

    @app.route("/")
    def home():
        return "Hello, World!"
    
    @app.get("/api/health")
    def health():
        return jsonify(status="ok")

    @app.route("/users")
    def list_users():
        with SessionLocal() as session:
            ...
    return app

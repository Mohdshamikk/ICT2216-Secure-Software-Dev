import os
from flask import Flask, jsonify
from flask_cors import CORS
from app.database_engine import SessionLocal

def create_app() -> Flask:
    app = Flask(__name__)

    CORS(app, origins=os.getenv("FRONTEND_URL", "http://localhost:5173"))

    @app.route("/")
    def home():
        return "Hello, World!"
    
    # curl.exe -X GET http://localhost:5000/api/health (internal)
    # curl.exe http://localhost/api/health (external)
    @app.get("/api/health")
    def health():
        return jsonify(status="ok")

    @app.route("/users")
    def list_users():
        with SessionLocal() as session:
            ...
    return app

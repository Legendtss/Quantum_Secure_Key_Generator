import sys
import os

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))

try:
    from app import app as flask_app
    app = flask_app
except ImportError as e:
    print(f"Error importing Flask app: {e}")
    from flask import Flask, jsonify

    app = Flask(__name__)

    @app.route("/api/health", methods=["GET"])
    def health_error():
        return jsonify({"error": str(e)}), 500

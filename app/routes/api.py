from flask import Blueprint, request, jsonify
from app.services import gemma

api_bp = Blueprint("api", __name__)


@api_bp.route("/health")
def health():
    return {"status": "ok"}


@api_bp.route("/gemma/translate", methods=["POST"])
def translate():
    data = request.get_json()
    text = data.get("text", "")
    languages = data.get("languages", ["en"])
    source = data.get("source_language", "en")
    if not text:
        return jsonify({"error": "text is required"}), 400
    try:
        return jsonify(gemma.translate(text, languages, source))
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@api_bp.route("/gemma/generate", methods=["POST"])
def generate():
    data = request.get_json()
    description = data.get("description", "")
    language = data.get("language", "en")
    if not description:
        return jsonify({"error": "description is required"}), 400
    try:
        return jsonify({"marketing_text": gemma.generate_marketing_text(description, language)})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@api_bp.route("/gemma/transcribe", methods=["POST"])
def transcribe():
    data = request.get_json()
    text = data.get("text", "")
    if not text:
        return jsonify({"error": "text is required"}), 400
    try:
        return jsonify({"transcription": gemma.transcribe_voice(text)})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

from flask import Blueprint, request, jsonify
from flask_login import login_required, current_user
from app import db
from app.models import Product
from app.services import gemma

api_bp = Blueprint("api", __name__)


@api_bp.route("/health")
def health():
    return {"status": "ok"}


@api_bp.route("/translate-one", methods=["POST"])
@login_required
def translate_one():
    data = request.get_json()
    product_id = data.get("product_id")
    lang = data.get("lang")
    source_lang = data.get("source_lang", "en")
    description = data.get("description", "")
    name = data.get("name", "")
    if not product_id or not lang or not description:
        return jsonify({"error": "missing fields"}), 400
    product = Product.query.filter_by(id=product_id, producer_id=current_user.id).first_or_404()
    try:
        desc_translated = gemma.translate_one(description, lang, source_lang)
        name_translated = gemma.translate_one(name, lang, source_lang) if name else name
        translations = dict(product.descriptions_translated or {})
        translations[lang] = desc_translated
        product.descriptions_translated = translations
        names = dict(product.names_translated or {})
        names[lang] = name_translated
        product.names_translated = names
        db.session.commit()
        return jsonify({"lang": lang, "description": desc_translated, "name": name_translated})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


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

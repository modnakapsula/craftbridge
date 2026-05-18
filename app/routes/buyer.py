from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from werkzeug.security import generate_password_hash, check_password_hash
from app import db
from app.models import Buyer, Product, Lead, Message
from app.services import gemma

buyer_bp = Blueprint("buyer", __name__)


@buyer_bp.route("/set-language/<lang>")
def set_language(lang):
    if lang in LANGUAGES:
        session["language"] = lang
    return redirect(request.referrer or url_for("buyer.shop"))

LANGUAGES = {
    "en": "English",
    "de": "Deutsch",
    "fr": "Français",
    "es": "Español",
    "it": "Italiano",
    "pt": "Português",
    "ar": "العربية (Arabic)",
    "ja": "日本語 (Japanese)",
    "zh": "中文 (Mandarin)",
    "ko": "한국어 (Korean)",
    "hi": "हिन्दी (Hindi)",
    "bn": "বাংলা (Bengali)",
    "sw": "Swahili",
    "tr": "Türkçe",
    "sr": "Srpski",
    "mk": "Македонски",
}

CATEGORIES = ["Clothing", "Knitwear", "Accessories", "Home Decor", "Jewelry", "Other"]


@buyer_bp.route("/")
def shop():
    category = request.args.get("category", "")
    search = request.args.get("search", "")
    sort = request.args.get("sort", "featured")
    lang = session.get("language", "en")

    query = Product.query.filter_by(is_active=True)
    if category:
        query = query.filter_by(category=category)
    if search:
        query = query.filter(Product.name.ilike(f"%{search}%"))

    if sort == "price_asc":
        query = query.order_by(Product.price.asc().nulls_last())
    elif sort == "price_desc":
        query = query.order_by(Product.price.desc().nulls_last())
    elif sort == "newest":
        query = query.order_by(Product.created_at.desc())
    else:
        query = query.order_by(Product.sort_order.asc().nulls_last(), Product.created_at.desc())

    products = query.all()
    return render_template("shop/index.html", products=products, category=category,
                           search=search, sort=sort, lang=lang, categories=CATEGORIES)


@buyer_bp.route("/product/<int:product_id>")
def product_detail(product_id):
    product = Product.query.get_or_404(product_id)
    lang = session.get("language", "en")
    description = product.descriptions_translated.get(lang) or product.description_original
    buyer_id = session.get("buyer_id")
    existing_lead = None
    if buyer_id:
        existing_lead = Lead.query.filter_by(product_id=product_id, buyer_id=buyer_id).first()
    return render_template("shop/product.html", product=product, description=description,
                           existing_lead=existing_lead, lang=lang)


@buyer_bp.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        name = request.form.get("name", "").strip()
        country = request.form.get("country", "")
        language = request.form.get("language", "en")

        if Buyer.query.filter_by(email=email).first():
            flash("Email already exists.", "danger")
            return render_template("shop/register.html", languages=LANGUAGES)

        buyer = Buyer(
            email=email,
            password_hash=generate_password_hash(password),
            name=name,
            country=country,
            language=language,
        )
        db.session.add(buyer)
        db.session.commit()
        session["buyer_id"] = buyer.id
        session["language"] = language
        return redirect(url_for("buyer.shop"))

    return render_template("shop/register.html", languages=LANGUAGES)


@buyer_bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        buyer = Buyer.query.filter_by(email=email).first()
        if buyer and check_password_hash(buyer.password_hash, password):
            session["buyer_id"] = buyer.id
            session["language"] = buyer.language
            return redirect(url_for("buyer.shop"))
        flash("Invalid email or password.", "danger")
    return render_template("shop/login.html")


@buyer_bp.route("/logout")
def logout():
    session.pop("buyer_id", None)
    session.pop("language", None)
    return redirect(url_for("buyer.shop"))


@buyer_bp.route("/lead/<int:product_id>", methods=["POST"])
def create_lead(product_id):
    buyer_id = session.get("buyer_id")
    if not buyer_id:
        flash("Please log in to continue.", "warning")
        return redirect(url_for("buyer.login"))

    product = Product.query.get_or_404(product_id)

    if Lead.query.filter_by(product_id=product_id, buyer_id=buyer_id).first():
        flash("You have already expressed interest in this product.", "info")
        return redirect(url_for("buyer.product_detail", product_id=product_id))

    db.session.add(Lead(
        product_id=product_id,
        buyer_id=buyer_id,
        producer_id=product.producer_id,
    ))
    db.session.commit()
    flash("Interest recorded! The maker will contact you shortly.", "success")
    return redirect(url_for("buyer.my_leads"))


@buyer_bp.route("/my-leads")
def my_leads():
    buyer_id = session.get("buyer_id")
    if not buyer_id:
        return redirect(url_for("buyer.login"))
    leads = Lead.query.filter_by(buyer_id=buyer_id).order_by(Lead.created_at.desc()).all()
    return render_template("shop/my_leads.html", leads=leads)


@buyer_bp.route("/messages/<int:lead_id>", methods=["GET", "POST"])
def messages(lead_id):
    buyer_id = session.get("buyer_id")
    if not buyer_id:
        return redirect(url_for("buyer.login"))

    lead = Lead.query.filter_by(id=lead_id, buyer_id=buyer_id).first_or_404()
    if request.method == "POST":
        content = request.form.get("content", "").strip()
        if content:
            buyer = Buyer.query.get(buyer_id)
            buyer_lang = buyer.language or "en"
            producer_lang = lead.producer.language or "en"
            try:
                translated = gemma.translate_one(content, producer_lang, buyer_lang) if buyer_lang != producer_lang else None
            except Exception:
                translated = None
            db.session.add(Message(
                lead_id=lead_id,
                sender_type="buyer",
                sender_id=buyer_id,
                content=content,
                translated_content=translated,
            ))
            db.session.commit()

    msgs = Message.query.filter_by(lead_id=lead_id).order_by(Message.created_at).all()
    return render_template("shop/messages.html", lead=lead, messages=msgs)

from flask import Flask, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from dotenv import load_dotenv
import os

load_dotenv()

db = SQLAlchemy()
login_manager = LoginManager()


def create_app():
    app = Flask(__name__)
    app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", "dev-secret-key")
    app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv("DATABASE_URL", "sqlite:///craftbridge.db")
    app.config["UPLOAD_FOLDER"] = os.path.join(app.root_path, "static", "uploads")

    db.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = "producer.login"

    from app.routes.producer import producer_bp
    from app.routes.buyer import buyer_bp
    from app.routes.api import api_bp

    app.register_blueprint(producer_bp, url_prefix="/producer")
    app.register_blueprint(buyer_bp, url_prefix="/shop")
    app.register_blueprint(api_bp, url_prefix="/api")

    from app.models import Producer, Buyer

    @login_manager.user_loader
    def load_user(user_id):
        if user_id.startswith("p_"):
            return Producer.query.get(int(user_id[2:]))
        elif user_id.startswith("b_"):
            return Buyer.query.get(int(user_id[2:]))
        return None

    @app.route("/")
    def index():
        return redirect(url_for("buyer.shop"))

    with app.app_context():
        db.create_all()

    return app

"""Create and configure the Campus Lost & Found Flask application."""

from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_wtf.csrf import CSRFProtect

db = SQLAlchemy()
csrf = CSRFProtect()


def create_app(config_class="config.Config"):
    """Build the app, load settings, and connect the database extension."""
    app = Flask(__name__)
    app.config.from_object(config_class)
    secret_key = app.config.get("SECRET_KEY", "")
    if not secret_key or secret_key.startswith("replace-this-with-"):
        raise RuntimeError(
            "Set a private SECRET_KEY in your .env file before starting the app."
        )
    db.init_app(app)
    csrf.init_app(app)

    # Import models so SQLAlchemy knows about their tables before create_all().
    from app import models  # noqa: F401
    from app.routes.auth import auth_bp
    from app.routes.items import items_bp
    from app.routes.claims import claims_bp
    from app.routes.dashboard import dashboard_bp
    from app.routes.admin import admin_bp
    app.register_blueprint(auth_bp)
    app.register_blueprint(items_bp)
    app.register_blueprint(claims_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(admin_bp)

    from flask import g, session
    from app.models import User

    @app.before_request
    def load_logged_in_user():
        """Load the signed-in user's database record for this request."""
        user_id = session.get("user_id")
        g.user = db.session.get(User, user_id) if user_id is not None else None

    @app.after_request
    def add_security_headers(response):
        """Set a few safe browser defaults on every response."""
        response.headers.setdefault("X-Content-Type-Options", "nosniff")
        response.headers.setdefault("X-Frame-Options", "DENY")
        response.headers.setdefault("Referrer-Policy", "same-origin")
        return response

    @app.context_processor
    def inject_template_globals():
        """Make the current user and CSRF helper available in every template."""
        from flask_wtf.csrf import generate_csrf

        return {"current_user": g.get("user"), "csrf_token": generate_csrf}

    @app.get("/")
    def index():
        from flask import render_template

        return render_template("home.html")

    return app

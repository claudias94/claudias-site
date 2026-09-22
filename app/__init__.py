import logging
import os
from logging.handlers import RotatingFileHandler

from flask import Flask, render_template, request
from werkzeug.middleware.proxy_fix import ProxyFix

from .config import Config
from .models import db
from .utils.security import csrf_token


def _file_logger(name, path):
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)
    path = os.path.abspath(path)
    for h in list(logger.handlers):  # drop handlers pointing at some other file
        if isinstance(h, RotatingFileHandler) and h.baseFilename != path:
            logger.removeHandler(h)
            h.close()
    if not any(isinstance(h, RotatingFileHandler) for h in logger.handlers):
        handler = RotatingFileHandler(path, maxBytes=512_000, backupCount=3,
                                      encoding="utf-8")
        handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(message)s"))
        logger.addHandler(handler)


def create_app(test_config=None):
    app = Flask(__name__)
    app.config.from_object(Config)
    if test_config:
        app.config.update(test_config)

    if not app.config["SECRET_KEY"]:
        raise RuntimeError("SECRET_KEY is not set. Copy .env.example to .env.")
    if app.config["IS_PRODUCTION"] and len(app.config["SECRET_KEY"]) < 32:
        raise RuntimeError("SECRET_KEY looks too short for production. "
                           "Generate a new one with: python3 -c "
                           "\"import secrets; print(secrets.token_hex(32))\"")

    proxies = app.config["TRUST_PROXY"]
    if proxies > 0:
        # Trust X-Forwarded-For/-Proto/-Host from exactly this many proxies.
        # Without this, request.remote_addr (used for rate limiting and the
        # audit log) would be the proxy's address for every visitor.
        app.wsgi_app = ProxyFix(app.wsgi_app, x_for=proxies, x_proto=proxies,
                                x_host=proxies)

    os.makedirs(app.instance_path, exist_ok=True)
    app.config.setdefault("DATABASE", os.path.join(app.instance_path, "leads.db"))
    app.config.setdefault("LOG_FILE", os.path.join(app.instance_path, "notifications.log"))
    app.config.setdefault("AUDIT_LOG_FILE", os.path.join(app.instance_path, "audit.log"))

    db.init_app(app)
    _file_logger("leads", app.config["LOG_FILE"])
    _file_logger("audit", app.config["AUDIT_LOG_FILE"])
    app.jinja_env.globals["csrf_token"] = csrf_token

    from .cli import create_admin_command, reset_admin_password_command
    app.cli.add_command(create_admin_command)
    app.cli.add_command(reset_admin_password_command)

    from .routes.main import bp as main_bp
    from .routes.contact import bp as contact_bp
    from .routes.admin import bp as admin_bp
    from .routes.api import bp as api_bp
    from .routes.seo import bp as seo_bp
    app.register_blueprint(main_bp)
    app.register_blueprint(contact_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(api_bp)
    app.register_blueprint(seo_bp)

    @app.context_processor
    def inject_site():
        c = app.config
        return {
            "site_name": c["SITE_NAME"],
            "site_title": c["SITE_TITLE"],
            "contact_email": c["CONTACT_EMAIL"],
            "github_url": c["GITHUB_URL"],
            "linkedin_url": c["LINKEDIN_URL"],
        }

    @app.after_request
    def security_headers(resp):
        resp.headers["Content-Security-Policy"] = (
            "default-src 'self'; img-src 'self' data:; "
            "style-src 'self'; script-src 'self'; "
            "frame-ancestors 'none'; base-uri 'self'; form-action 'self'"
        )
        resp.headers["X-Content-Type-Options"] = "nosniff"
        resp.headers["X-Frame-Options"] = "DENY"
        resp.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        resp.headers["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"
        if request.path.startswith("/admin"):
            resp.headers["Cache-Control"] = "no-store"
            resp.headers["X-Robots-Tag"] = "noindex, nofollow"
        return resp

    def page(title, message, code):
        return render_template("placeholder.html", title=title, message=message), code

    @app.errorhandler(400)
    def bad_request(e):
        return page("Request could not be verified",
                    "Your form session may have expired. Please go back, "
                    "reload the page and try again.", 400)

    @app.errorhandler(404)
    def not_found(e):
        return page("Page not found", "That page doesn't exist.", 404)

    @app.errorhandler(413)
    def too_large(e):
        return page("Message too large", "That request was too large to accept.", 413)

    @app.errorhandler(429)
    def too_many(e):
        return page("Too many requests",
                    "Several requests were sent in a short time. Please wait a "
                    "while and try again, or email me directly.", 429)

    @app.errorhandler(500)
    def server_error(e):
        return page("Something went wrong", "Please try again shortly.", 500)

    return app

import os
from datetime import timedelta

from dotenv import load_dotenv

load_dotenv()

_TRUTHY = {"1", "true", "yes", "on"}


def _bool_env(name, default=False):
    val = os.environ.get(name)
    if val is None:
        return default
    return val.strip().lower() in _TRUTHY


class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY")
    FLASK_ENV = os.environ.get("FLASK_ENV", "development")
    IS_PRODUCTION = FLASK_ENV == "production"

    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"
    # Only sent over HTTPS in production. Requires the site to actually be
    # served over HTTPS, or the browser will silently refuse to set the
    # session cookie and sign-in will appear broken.
    SESSION_COOKIE_SECURE = IS_PRODUCTION
    PERMANENT_SESSION_LIFETIME = timedelta(hours=2)  # admin idle timeout
    ADMIN_MAX_SESSION_SECONDS = 8 * 3600             # admin absolute timeout
    MAX_CONTENT_LENGTH = 64 * 1024  # reject request bodies over 64 KB

    # Set to the number of reverse proxies (load balancer, nginx, the
    # platform's own edge, ...) sitting in front of this app, so the real
    # visitor IP is read from X-Forwarded-For instead of the proxy's own
    # address. 0 (the default) means "no proxy in front of me" — correct
    # for local development and for hosts that route traffic to the app
    # directly. Set TRUST_PROXY=1 once deployed behind exactly one proxy;
    # ask your host if you're not sure how many hops are in front of you.
    TRUST_PROXY = int(os.environ.get("TRUST_PROXY", "0"))

    SITE_NAME = "Claudias Musavini Misiko"
    SITE_TITLE = "IT & Cybersecurity Professional"
    CONTACT_EMAIL = "claudiasmisiko@gmail.com"
    GITHUB_URL = "https://github.com/claudias94"
    LINKEDIN_URL = "https://linkedin.com/in/claudias-musavini-3b0918116"

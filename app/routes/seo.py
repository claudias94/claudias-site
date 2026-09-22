from flask import Blueprint, Response, url_for

from ..utils.projects import PROJECT_LIST

bp = Blueprint("seo", __name__)

STATIC_PAGES = ["main.index", "main.services", "main.projects", "main.about",
                "contact.form"]


@bp.route("/robots.txt")
def robots():
    lines = [
        "User-agent: *",
        "Disallow: /admin",
        "Disallow: /api",
        "Disallow: /contact/thanks",
        f"Sitemap: {url_for('seo.sitemap', _external=True)}",
    ]
    return Response("\n".join(lines) + "\n", mimetype="text/plain")


@bp.route("/sitemap.xml")
def sitemap():
    urls = [url_for(ep, _external=True) for ep in STATIC_PAGES]
    urls += [url_for("main.project_detail", slug=p["slug"], _external=True)
            for p in PROJECT_LIST]
    body = ['<?xml version="1.0" encoding="UTF-8"?>',
           '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
    for u in urls:
        body.append(f"<url><loc>{u}</loc></url>")
    body.append("</urlset>")
    return Response("\n".join(body), mimetype="application/xml")

from flask import Blueprint, render_template, abort
from ..utils.content import CATEGORIES, PROBLEMS, AUDIENCES, STEPS, TRUST
from ..utils.projects import PROJECT_LIST, PROJECTS, STACK

bp = Blueprint("main", __name__)

JOURNEY = [
    {"period": "Current", "title": "IT Officer, Kenya School of Government",
     "text": "Working primarily on networking and technical infrastructure "
             "operations: supporting network connectivity, troubleshooting "
             "network-related issues, and helping run the institution's IT "
             "environment.",
     "placeholder": False},
    {"period": "Ongoing", "title": "Systems & Server Administration",
     "text": "Holds administrative privileges on the institution's servers, "
             "giving practical, hands-on exposure to server-side operations "
             "and systems administration.",
     "placeholder": False},
    {"period": "Ongoing", "title": "Cybersecurity Practice",
     "text": "Security monitoring, log analysis, incident response, digital "
             "forensics, IOC analysis, vulnerability assessment and security "
             "hardening. See Featured Projects for the SOC Log Analyzer and "
             "the incident response laboratory.",
     "placeholder": False},
    {"period": "Ongoing", "title": "Software & Web Development",
     "text": "Building Python and Flask applications, REST APIs, dashboards "
             "and internal business tools. See Featured Projects for KIAMS.",
     "placeholder": False},
    {"period": "Current", "title": "Continuous Professional Development",
     "text": "Continuing to build practical capability across IT "
             "infrastructure, cybersecurity and software development.",
     "placeholder": False},
]

BACKGROUND = ("Bachelor's Degree in Computer Security and Forensics "
             "(Cybersecurity), Kabarak University.")

APPROACH_STEPS = ["Understand the problem", "Analyze the environment",
                  "Build or implement the solution", "Test it", "Secure it",
                  "Document it"]


@bp.route("/")
def index():
    return render_template("index.html", categories=CATEGORIES, problems=PROBLEMS,
                           audiences=AUDIENCES, steps=STEPS, trust=TRUST,
                           projects=PROJECT_LIST, stack=STACK)


@bp.route("/about")
def about():
    return render_template("about.html", journey=JOURNEY, background=BACKGROUND,
                           approach_steps=APPROACH_STEPS)


@bp.route("/services")
def services():
    return render_template("services.html", categories=CATEGORIES)


@bp.route("/projects")
def projects():
    return render_template("projects.html", projects=PROJECT_LIST)


@bp.route("/projects/<slug>")
def project_detail(slug):
    project = PROJECTS.get(slug)
    if not project:
        abort(404)
    return render_template("project_detail.html", p=project)

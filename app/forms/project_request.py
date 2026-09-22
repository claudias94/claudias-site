import re

PROJECT_TYPES = ["Website", "Web Application", "Python/Flask", "IT Support",
                 "Networking", "Cybersecurity", "Security Assessment",
                 "Automation", "Dashboard", "Incident Response", "Other"]
BUDGETS = ["Not sure yet", "Under KES 20,000", "KES 20,000 to 50,000",
           "KES 50,000 to 150,000", "KES 150,000 to 500,000", "Above KES 500,000"]
TIMELINES = ["As soon as possible", "Within 2 weeks", "Within a month",
             "1 to 3 months", "Flexible"]
CONTACT_METHODS = ["Email", "Phone call", "WhatsApp"]
PHONE_METHODS = {"Phone call", "WhatsApp"}

FIELDS = ["name", "email", "phone", "organization", "project_type", "budget",
          "timeline", "contact_method", "description", "source_topic"]

_EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]{2,}$")
_PHONE_RE = re.compile(r"^\+?[0-9][0-9 ()\-]{6,19}$")
_CTRL_RE = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]")

# Which project type a "Discuss This Project" link should preselect.
# Order matters: the first matching rule wins.
_TOPIC_RULES = [
    (("incident", "forensic", "ioc analysis"), "Incident Response"),
    (("security assessment", "vulnerability"), "Security Assessment"),
    (("cyber", "security", "soc ", "log analysis"), "Cybersecurity"),
    (("network", "wi-fi", "wifi", "printer", "cctv"), "Networking"),
    (("flask", "python"), "Python/Flask"),
    (("dashboard",), "Dashboard"),
    (("automation",), "Automation"),
    (("website",), "Website"),
    (("configuration", "troubleshooting", "support", "server",
      "documentation", "windows"), "IT Support"),
    (("system", "application", "api", "authentication", "database",
      "access"), "Web Application"),
]


def clean(value, multiline=False):
    """Remove control characters and normalise whitespace."""
    value = _CTRL_RE.sub("", value or "")
    if multiline:
        return value.replace("\r\n", "\n").replace("\r", "\n").strip()
    return " ".join(value.split())


def guess_project_type(topic):
    t = (topic or "").lower()
    for words, project_type in _TOPIC_RULES:
        if any(w in t for w in words):
            return project_type
    return ""


def validate(form):
    """Return (clean_values, errors). errors maps field name -> message."""
    v = {k: clean(form.get(k, ""), multiline=(k == "description")) for k in FIELDS}
    v["source_topic"] = v["source_topic"][:100]
    errors = {}

    if not 2 <= len(v["name"]) <= 100:
        errors["name"] = "Please enter your name (2 to 100 characters)."
    if len(v["email"]) > 254 or not _EMAIL_RE.match(v["email"]):
        errors["email"] = "Please enter a valid email address."
    if len(v["organization"]) > 150:
        errors["organization"] = "Please keep this under 150 characters."
    if v["project_type"] not in PROJECT_TYPES:
        errors["project_type"] = "Please choose a project type."
    if v["budget"] not in BUDGETS:
        errors["budget"] = "Please choose a budget range."
    if v["timeline"] not in TIMELINES:
        errors["timeline"] = "Please choose a timeline."
    if v["contact_method"] not in CONTACT_METHODS:
        errors["contact_method"] = "Please choose a contact method."
    if not 20 <= len(v["description"]) <= 3000:
        errors["description"] = "Please describe your project in 20 to 3000 characters."

    if v["phone"] and not _PHONE_RE.match(v["phone"]):
        errors["phone"] = "Please enter a valid number, for example +254 700 000 000."
    elif v["contact_method"] in PHONE_METHODS and not v["phone"]:
        errors["phone"] = "A phone number is needed for that contact method."

    return v, errors

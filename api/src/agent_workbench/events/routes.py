from flask import Blueprint

bp = Blueprint("events", __name__, url_prefix="/api")

# Routes implemented in Implementation Phase: Core API Modules
# Event routes: /api/projects/<project_id>/events and /api/events (create)

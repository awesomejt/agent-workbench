from flask import Blueprint

bp = Blueprint("project_status", __name__, url_prefix="/api/projects")

# Routes implemented in Implementation Phase: Core API Modules
# URL prefix shared with projects; status routes are nested under /api/projects/<project_id>/status

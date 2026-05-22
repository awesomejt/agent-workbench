from flask import Blueprint

bp = Blueprint("project_sections", __name__, url_prefix="/api/projects")

# Routes implemented in Implementation Phase: Core API Modules
# Section routes are nested under /api/projects/<project_id>/sections

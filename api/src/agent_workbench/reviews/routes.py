from flask import Blueprint

bp = Blueprint("reviews", __name__, url_prefix="/api")

# Routes implemented in Implementation Phase: Core API Modules
# Review routes: /api/projects/<project_id>/reviews and /api/reviews/<review_id>

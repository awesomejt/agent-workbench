from flask import Blueprint

bp = Blueprint("tasks", __name__, url_prefix="/api")

# Routes implemented in Implementation Phase: Core API Modules
# Task routes: /api/projects/<project_id>/tasks and /api/tasks/<task_id>/...

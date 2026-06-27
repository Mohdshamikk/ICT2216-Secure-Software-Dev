from flask import Blueprint

users_bp = Blueprint('users', __name__, url_prefix='/api/users')

# FR-03: GET    /api/users/me
# FR-04: PATCH  /api/users/me
# FR-04: PATCH  /api/users/me/password
# FR-05: DELETE /api/users/me

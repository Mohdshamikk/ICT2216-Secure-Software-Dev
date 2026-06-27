from flask import Blueprint

admin_bp = Blueprint('admin', __name__, url_prefix='/api/admin')

# FR-11: GET    /api/admin/users
# FR-11: PATCH  /api/admin/users/:id/status
# FR-11: DELETE /api/admin/users/:id
# FR-11: PATCH  /api/admin/users/:id/role
# SR-16: GET    /api/admin/audit-logs

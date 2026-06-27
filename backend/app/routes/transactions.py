from flask import Blueprint

transactions_bp = Blueprint('transactions', __name__, url_prefix='/api/transactions')

# FR-06: GET    /api/transactions
# FR-06: POST   /api/transactions
# FR-06: PATCH  /api/transactions/:id
# FR-06: DELETE /api/transactions/:id
# FR-08: GET    /api/dashboard
# FR-13: GET    /api/transactions/export

from __future__ import annotations

from datetime import datetime

from flask import Blueprint, g, jsonify, request

from app.middleware.auth import require_auth
from app.models import Category, Transaction

transactions_bp = Blueprint('transactions', __name__, url_prefix='/api/transactions')

# FR-06: GET    /api/transactions
# TODO: Wen Yuan — Phase 5
#   POST   /api/transactions
#   PATCH  /api/transactions/:id
#   DELETE /api/transactions/:id
#   GET    /api/dashboard      (FR-08)
#   GET    /api/transactions/export  (FR-13)


def _parse_date_param(name: str):
    raw = request.args.get(name)
    if not raw:
        return None
    try:
        return datetime.strptime(raw, '%Y-%m-%d').date()
    except ValueError:
        return None


# ---------------------------------------------------------------------------
# FR-06: List own transactions (object-level scoped to current user)
# ---------------------------------------------------------------------------

@transactions_bp.get('')
@require_auth
def list_transactions():
    query = (
        Transaction.query
        .filter_by(user_id=g.current_user.id)
    )

    date_from = _parse_date_param('from')
    date_to = _parse_date_param('to')
    if date_from:
        query = query.filter(Transaction.transaction_date >= date_from)
    if date_to:
        query = query.filter(Transaction.transaction_date <= date_to)

    transactions = (
        query.join(Category, Transaction.category_id == Category.id)
        .order_by(Transaction.transaction_date.desc(), Transaction.created_at.desc())
        .all()
    )

    return jsonify([
        {
            'id': str(t.id),
            'transaction_date': t.transaction_date.isoformat(),
            'amount': str(t.amount),
            'type': t.category.type,
            'category': t.category.name,
            'merchant_name': t.merchant_name,
            'description': t.description,
        }
        for t in transactions
    ]), 200

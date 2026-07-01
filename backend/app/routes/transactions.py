from __future__ import annotations

import uuid
from datetime import datetime, timedelta
from decimal import Decimal, InvalidOperation

from flask import Blueprint, g, jsonify, request
from sqlalchemy import or_

from app.extensions import db
from app.middleware.auth import require_auth
from app.models import Category, Transaction
from app.services.audit import log_event

transactions_bp = Blueprint('transactions', __name__, url_prefix='/api/transactions')

# FR-06: GET /api/transactions, POST /api/transactions
# FR-06: PATCH /api/transactions/:id, DELETE /api/transactions/:id
# TODO: Wen Yuan — Phase 5
#   GET    /api/dashboard      (FR-08)
#   GET    /api/transactions/export  (FR-13)

# transaction_date may not be dated further ahead than this many days.
_MAX_FUTURE_DAYS = 1

# Fields a client is allowed to change via PATCH.
_EDITABLE_FIELDS = {'transaction_date', 'amount', 'category_id', 'merchant_name', 'description'}


def _client_ip() -> str:
    return request.headers.get('X-Real-IP', request.remote_addr) or '0.0.0.0'


def _parse_date_param(name: str):
    raw = request.args.get(name)
    if not raw:
        return None
    try:
        return datetime.strptime(raw, '%Y-%m-%d').date()
    except ValueError:
        return None


def _serialize(t: Transaction) -> dict:
    return {
        'id': str(t.id),
        'transaction_date': t.transaction_date.isoformat(),
        'amount': str(t.amount),
        'type': t.category.type,
        'category': t.category.name,
        'category_id': str(t.category_id),
        'merchant_name': t.merchant_name,
        'description': t.description,
    }


# ---------------------------------------------------------------------------
# Field validators — shared by create and update. Each returns (ok, value_or_error).
# ---------------------------------------------------------------------------

def _validate_tx_date(raw):
    if not isinstance(raw, str):
        return False, 'transaction_date must be YYYY-MM-DD'
    try:
        tx_date = datetime.strptime(raw, '%Y-%m-%d').date()
    except ValueError:
        return False, 'transaction_date must be YYYY-MM-DD'
    if tx_date > (datetime.utcnow().date() + timedelta(days=_MAX_FUTURE_DAYS)):
        return False, 'transaction_date is too far in the future'
    return True, tx_date


def _validate_amount(raw):
    if isinstance(raw, float):
        # Reject float — precision loss. Client must send amount as a string.
        return False, 'amount must be sent as a string, not a number'
    if not isinstance(raw, (str, int)):
        return False, 'amount must be a string or integer'
    try:
        amount = Decimal(str(raw))
    except (InvalidOperation, ValueError):
        return False, 'amount must be a valid decimal'
    if not amount.is_finite() or amount <= 0:
        return False, 'amount must be a positive decimal'
    if amount.as_tuple().exponent < -2:
        return False, 'amount may have at most 2 decimal places'
    if amount >= Decimal('10000000000'):  # Numeric(12, 2) -> max 10 integer digits
        return False, 'amount is too large'
    return True, amount


def _resolve_category(raw, user):
    """Return (True, Category) for a global or user-owned category, else (False, error)."""
    if not isinstance(raw, str):
        return False, 'category_id must be a valid UUID'
    try:
        category_uuid = uuid.UUID(raw)
    except ValueError:
        return False, 'category_id must be a valid UUID'

    category = Category.query.filter(
        Category.id == category_uuid,
        or_(Category.user_id.is_(None), Category.user_id == user.id),
    ).first()
    if category is None:
        return False, 'category not found'
    return True, category


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

    return jsonify([_serialize(t) for t in transactions]), 200


# ---------------------------------------------------------------------------
# FR-06: Create a transaction (manual entry)
# ---------------------------------------------------------------------------

@transactions_bp.post('')
@require_auth
def create_transaction():
    user = g.current_user
    ip = _client_ip()
    ua = request.headers.get('User-Agent')

    data = request.get_json(silent=True) or {}

    # --- transaction_date: valid ISO date, not in the far future ------------
    raw_date = data.get('transaction_date')
    if not isinstance(raw_date, str):
        return jsonify({'error': 'transaction_date is required'}), 400
    try:
        tx_date = datetime.strptime(raw_date, '%Y-%m-%d').date()
    except ValueError:
        return jsonify({'error': 'transaction_date must be YYYY-MM-DD'}), 400
    if tx_date > (datetime.utcnow().date() + timedelta(days=_MAX_FUTURE_DAYS)):
        return jsonify({'error': 'transaction_date is too far in the future'}), 400

    # --- amount: parse as Decimal from string, never float -----------------
    raw_amount = data.get('amount')
    if isinstance(raw_amount, float):
        # Reject float — precision loss. Client must send amount as a string.
        return jsonify({'error': 'amount must be sent as a string, not a number'}), 400
    if not isinstance(raw_amount, (str, int)):
        return jsonify({'error': 'amount is required'}), 400
    try:
        amount = Decimal(str(raw_amount))
    except (InvalidOperation, ValueError):
        return jsonify({'error': 'amount must be a valid decimal'}), 400
    if not amount.is_finite() or amount <= 0:
        return jsonify({'error': 'amount must be a positive decimal'}), 400
    if amount.as_tuple().exponent < -2:
        return jsonify({'error': 'amount may have at most 2 decimal places'}), 400
    if amount >= Decimal('10000000000'):  # Numeric(12, 2) -> max 10 integer digits
        return jsonify({'error': 'amount is too large'}), 400

    # --- category_id: valid UUID, global or owned by current user ----------
    raw_category = data.get('category_id')
    if not isinstance(raw_category, str):
        return jsonify({'error': 'category_id is required'}), 400
    try:
        category_uuid = uuid.UUID(raw_category)
    except ValueError:
        return jsonify({'error': 'category_id must be a valid UUID'}), 400

    category = Category.query.filter(
        Category.id == category_uuid,
        or_(Category.user_id.is_(None), Category.user_id == user.id),
    ).first()
    if category is None:
        return jsonify({'error': 'category not found'}), 404

    # --- optional string fields -------------------------------------------
    merchant_name = data.get('merchant_name')
    if merchant_name is not None:
        if not isinstance(merchant_name, str):
            return jsonify({'error': 'merchant_name must be a string'}), 400
        merchant_name = merchant_name.strip()[:255] or None

    description = data.get('description')
    if description is not None:
        if not isinstance(description, str):
            return jsonify({'error': 'description must be a string'}), 400
        description = description.strip() or None

    transaction = Transaction(
        user_id=user.id,
        category_id=category.id,
        transaction_date=tx_date,
        amount=amount,
        merchant_name=merchant_name,
        description=description,
    )
    db.session.add(transaction)
    db.session.commit()

    log_event(
        'TRANSACTION_CREATED', 'SUCCESS', ip,
        user_id=user.id, resource_id=transaction.id, user_agent=ua,
    )

    return jsonify(_serialize(transaction)), 201


# ---------------------------------------------------------------------------
# FR-06: Update a transaction (partial, object-level scoped to current user)
# ---------------------------------------------------------------------------

@transactions_bp.patch('/<transaction_id>')
@require_auth
def update_transaction(transaction_id):
    user = g.current_user
    ip = _client_ip()
    ua = request.headers.get('User-Agent')

    # Object-level check: id AND user_id. Unknown/foreign id -> 404 (never reveals existence).
    try:
        tx_uuid = uuid.UUID(transaction_id)
    except ValueError:
        return jsonify({'error': 'transaction not found'}), 404

    transaction = Transaction.query.filter_by(id=tx_uuid, user_id=user.id).first()
    if transaction is None:
        return jsonify({'error': 'transaction not found'}), 404

    data = request.get_json(silent=True) or {}
    if not (_EDITABLE_FIELDS & data.keys()):
        return jsonify({'error': 'no editable fields provided'}), 400

    if 'transaction_date' in data:
        ok, val = _validate_tx_date(data.get('transaction_date'))
        if not ok:
            return jsonify({'error': val}), 400
        transaction.transaction_date = val

    if 'amount' in data:
        ok, val = _validate_amount(data.get('amount'))
        if not ok:
            return jsonify({'error': val}), 400
        transaction.amount = val

    if 'category_id' in data:
        ok, val = _resolve_category(data.get('category_id'), user)
        if not ok:
            return jsonify({'error': val}), 404 if val == 'category not found' else 400
        transaction.category_id = val.id

    if 'merchant_name' in data:
        raw = data.get('merchant_name')
        if raw is None:
            transaction.merchant_name = None
        elif not isinstance(raw, str):
            return jsonify({'error': 'merchant_name must be a string'}), 400
        else:
            transaction.merchant_name = raw.strip()[:255] or None

    if 'description' in data:
        raw = data.get('description')
        if raw is None:
            transaction.description = None
        elif not isinstance(raw, str):
            return jsonify({'error': 'description must be a string'}), 400
        else:
            transaction.description = raw.strip() or None

    db.session.commit()

    log_event(
        'TRANSACTION_UPDATED', 'SUCCESS', ip,
        user_id=user.id, resource_id=transaction.id, user_agent=ua,
    )

    return jsonify(_serialize(transaction)), 200


# ---------------------------------------------------------------------------
# FR-06: Delete a transaction (object-level scoped to current user)
# ---------------------------------------------------------------------------

@transactions_bp.delete('/<transaction_id>')
@require_auth
def delete_transaction(transaction_id):
    user = g.current_user
    ip = _client_ip()
    ua = request.headers.get('User-Agent')

    try:
        tx_uuid = uuid.UUID(transaction_id)
    except ValueError:
        return jsonify({'error': 'transaction not found'}), 404

    transaction = Transaction.query.filter_by(id=tx_uuid, user_id=user.id).first()
    if transaction is None:
        return jsonify({'error': 'transaction not found'}), 404

    # Audit log written before deletion so resource_id survives.
    log_event(
        'TRANSACTION_DELETED', 'SUCCESS', ip,
        user_id=user.id, resource_id=transaction.id, user_agent=ua,
    )

    db.session.delete(transaction)
    db.session.commit()

    return '', 204

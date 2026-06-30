from __future__ import annotations

import os
from uuid import uuid4

from flask import Blueprint, current_app, g, jsonify, request

from app import limiter
from app.extensions import db
from app.middleware.auth import require_auth
from app.models import BankStatement, Category, Transaction
from app.services.audit import log_event
from app.services.statement_parser import ParseError, parse_csv, parse_pdf
from app.services.storage import StorageError, upload_statement
from app.utils.encryption import hash_file_sha256

statements_bp = Blueprint('statements', __name__, url_prefix='/api/statements')

# FR-07: POST /api/statements/upload
# FR-07: GET  /api/statements


def _ip() -> str:
    return request.headers.get('X-Real-IP', request.remote_addr) or '0.0.0.0'


def _ua() -> str:
    return (request.headers.get('User-Agent') or '')[:500]


def _other_categories() -> tuple[Category | None, Category | None]:
    """Resolve the two global fallback categories used for imported transactions."""
    expense = Category.query.filter_by(user_id=None, name='Other Expense', type='EXPENSE').first()
    income = Category.query.filter_by(user_id=None, name='Other Income', type='INCOME').first()
    return expense, income


# ---------------------------------------------------------------------------
# FR-07: Upload + parse + import a bank statement
# ---------------------------------------------------------------------------

@statements_bp.post('/upload')
@require_auth
@limiter.limit('20 per hour')
def upload():
    ip, ua = _ip(), _ua()
    user = g.current_user

    file = request.files.get('file')
    if file is None or not file.filename:
        return jsonify({'error': 'No file provided'}), 400

    original_name = file.filename
    ext = os.path.splitext(original_name)[1].lower().lstrip('.')

    # 1. Size check — baseline byte count (MAX_CONTENT_LENGTH also rejects at the WSGI layer).
    #    TODO: Abdillah — Phase 4 SR-08: dedicated pre-stream 413 that cannot be bypassed by omitting Content-Length.
    file_bytes = file.read()
    if not file_bytes:
        return jsonify({'error': 'Empty file'}), 400
    if len(file_bytes) > current_app.config['MAX_UPLOAD_SIZE_MB'] * 1024 * 1024:
        log_event('STATEMENT_UPLOADED', 'FAILURE', ip, user_id=user.id, user_agent=ua)
        return jsonify({'error': 'File too large'}), 413

    # 2. Type check — baseline extension allowlist.
    #    TODO: HC Y — Phase 4 SR-03: validate magic bytes with python-magic, not just the extension.
    if ext not in current_app.config['ALLOWED_EXTENSIONS']:
        log_event('STATEMENT_UPLOADED', 'FAILURE', ip, user_id=user.id, user_agent=ua)
        return jsonify({'error': 'Unsupported file type'}), 415

    # 3. Random server-generated object path (never trust the client filename).
    content_type = 'text/csv' if ext == 'csv' else 'application/pdf'
    object_path = f'{user.id}/{uuid4()}.{ext}'

    # 4. Store the raw file in the private Supabase bucket.
    try:
        storage_path = upload_statement(object_path, file_bytes, content_type)
    except StorageError:
        current_app.logger.exception('statement storage upload failed')
        log_event('STATEMENT_UPLOADED', 'FAILURE', ip, user_id=user.id, user_agent=ua)
        return jsonify({'error': 'Failed to store file'}), 502

    # 5. Integrity hash (reuse existing util).
    file_hash = hash_file_sha256(file_bytes)

    # 6. Parse.
    status = 'PROCESSED'
    rows: list[dict] = []
    skipped = 0
    try:
        rows, skipped = parse_csv(file_bytes) if ext == 'csv' else parse_pdf(file_bytes)
    except ParseError:
        status = 'FAILED'
    if not rows:
        status = 'FAILED'

    # 7. Import statement + transactions in a single DB transaction.
    statement = BankStatement(
        user_id=user.id,
        file_name=original_name[:255],
        storage_path=storage_path,
        file_hash=file_hash,
        status=status,
        # account_number_encrypted left null — TODO: extract account number then encrypt_field
    )
    db.session.add(statement)
    db.session.flush()  # assign statement.id before linking transactions

    imported = 0
    if status == 'PROCESSED':
        cat_expense, cat_income = _other_categories()
        if not cat_expense or not cat_income:
            db.session.rollback()
            current_app.logger.error('Global "Other" categories missing from categories table')
            log_event('STATEMENT_UPLOADED', 'FAILURE', ip, user_id=user.id, user_agent=ua)
            return jsonify({'error': 'Server configuration error'}), 500

        for r in rows:
            category = cat_expense if r['is_expense'] else cat_income
            db.session.add(Transaction(
                user_id=user.id,
                statement_id=statement.id,
                category_id=category.id,
                transaction_date=r['transaction_date'],
                amount=r['amount'],
                merchant_name=r['merchant_name'],
                description=r['description'],
            ))
            imported += 1

    try:
        db.session.commit()
    except Exception:
        db.session.rollback()
        current_app.logger.exception('failed to import statement transactions')
        log_event('STATEMENT_UPLOADED', 'FAILURE', ip, user_id=user.id, user_agent=ua)
        return jsonify({'error': 'Failed to import transactions'}), 500

    log_event(
        'STATEMENT_UPLOADED',
        'SUCCESS' if status == 'PROCESSED' else 'FAILURE',
        ip, user_id=user.id, resource_id=statement.id, user_agent=ua,
    )

    return jsonify({
        'statement_id': str(statement.id),
        'status': status,
        'imported_count': imported,
        'skipped_count': skipped,
    }), 201


# ---------------------------------------------------------------------------
# FR-07: List current user's statements
# ---------------------------------------------------------------------------

@statements_bp.get('')
@require_auth
def list_statements():
    statements = (
        BankStatement.query
        .filter_by(user_id=g.current_user.id)
        .order_by(BankStatement.uploaded_at.desc())
        .all()
    )
    # storage_path and file_hash are deliberately never returned.
    return jsonify([
        {
            'id': str(s.id),
            'file_name': s.file_name,
            'status': s.status,
            'uploaded_at': s.uploaded_at.isoformat(),
        }
        for s in statements
    ]), 200

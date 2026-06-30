from __future__ import annotations

import csv
import io
import os
from pathlib import Path
from uuid import uuid4

import magic
from flask import Blueprint, current_app, g, jsonify, request

from app import limiter
from app.extensions import db
from app.middleware.auth import require_auth
from app.models import BankStatement, Category, Transaction
from app.services.audit import log_event
from app.services.statement_parser import ParseError, parse_csv, parse_pdf
from app.services.storage import StorageError, fetch_statement, upload_statement
from app.utils.encryption import hash_file_sha256

statements_bp = Blueprint('statements', __name__, url_prefix='/api/statements')

# FR-07: POST /api/statements/upload
# FR-07: GET  /api/statements


def _uploaded_file_size_bytes(uploaded_file) -> int:
	stream = uploaded_file.stream
	current_position = stream.tell()
	stream.seek(0, io.SEEK_END)
	size = stream.tell()
	stream.seek(current_position)
	return size


def _uploaded_file_mime_type(uploaded_file) -> str | None:
	stream = uploaded_file.stream
	current_position = stream.tell()
	stream.seek(0)
	sample = stream.read(8192)
	stream.seek(current_position)
	mime_type = magic.from_buffer(sample, mime=True)

	if mime_type == 'application/pdf' or sample.startswith(b'%PDF-'):
		return 'application/pdf'

	if mime_type in {'text/csv', 'text/plain'}:
		try:
			sample_text = sample.decode('utf-8-sig')
		except UnicodeDecodeError:
			return None

		try:
			dialect = csv.Sniffer().sniff(sample_text, delimiters=',;\t|')
			rows = list(csv.reader(io.StringIO(sample_text), dialect))
		except csv.Error:
			return None

		if rows and any(len(row) > 1 for row in rows):
			return 'text/csv'

		return None

	if b'\x00' in sample:
		return None

	return None


def _server_generated_filename(original_filename: str) -> str:
	return f'{uuid4()}{Path(original_filename).suffix}'


def _uploaded_file_bytes(uploaded_file) -> bytes:
	stream = uploaded_file.stream
	current_position = stream.tell()
	stream.seek(0)
	file_bytes = stream.read()
	stream.seek(current_position)
	return file_bytes



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
    max_upload_size_bytes = current_app.config['MAX_UPLOAD_SIZE_MB'] * 1024 * 1024
    if _uploaded_file_size_bytes(file) > max_upload_size_bytes:
        log_event('STATEMENT_UPLOADED', 'FAILURE', ip, user_id=user.id, user_agent=ua)
        return jsonify({'error': 'File too large'}), 413

    # 2. MIME check — validate magic bytes.
    mime_type = _uploaded_file_mime_type(file)
    if mime_type not in {'text/csv', 'application/pdf'}:
        log_event('STATEMENT_UPLOADED', 'FAILURE', ip, user_id=user.id, user_agent=ua)
        return jsonify({'error': 'Unsupported file type'}), 415

    # 3. Generate random server-generated filename (never trust client filename).
    server_filename = _server_generated_filename(original_name)
    content_type = 'text/csv' if ext == 'csv' else 'application/pdf'

    # 4. Read and store the raw file in the private Supabase bucket.
    file_bytes = _uploaded_file_bytes(file)
    if not file_bytes:
        return jsonify({'error': 'Empty file'}), 400

    object_path = f'{user.id}/{server_filename}'
    try:
        storage_path = upload_statement(object_path, file_bytes, content_type)
    except StorageError:
        current_app.logger.exception('statement storage upload failed')
        log_event('STATEMENT_UPLOADED', 'FAILURE', ip, user_id=user.id, user_agent=ua)
        return jsonify({'error': 'Failed to store file'}), 502

    # 5. Compute integrity hash.
    file_hash = hash_file_sha256(file_bytes)

    # 6. Parse transactions from file.
    status = 'PROCESSED'
    rows: list[dict] = []
    skipped = 0
    try:
        rows, skipped = parse_csv(file_bytes) if ext == 'csv' else parse_pdf(file_bytes)
    except ParseError:
        status = 'FAILED'
    if not rows:
        status = 'FAILED'

    # 7. Insert statement and transactions in a single DB transaction.
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

@statements_bp.get('/<statement_id>')
@require_auth
def get_statement(statement_id):
  
    ip, ua = _ip(), _ua()
    user = g.current_user

    # Fetch statement (verify ownership and get stored hash)
    statement = BankStatement.query.filter_by(
        id=statement_id,
        user_id=user.id
    ).first()

    if not statement:
        return jsonify({'error': 'Statement not found'}), 404

    # Retrieve file from Supabase
    try:
        file_bytes = fetch_statement(statement.storage_path)
    except StorageError:
        current_app.logger.exception('statement retrieval failed')
        log_event('STATEMENT_RETRIEVED', 'FAILURE', ip, user_id=user.id, user_agent=ua)
        return jsonify({'error': 'Failed to retrieve file'}), 502

    # Verify integrity by comparing hashes
    computed_hash = hash_file_sha256(file_bytes)
    if computed_hash != statement.file_hash:
        current_app.logger.error(f'Hash mismatch for statement {statement.id}')
        log_event('STATEMENT_RETRIEVED', 'FAILURE', ip, user_id=user.id, user_agent=ua)
        return jsonify({'error': 'File integrity check failed'}), 409

    log_event('STATEMENT_RETRIEVED', 'SUCCESS', ip, user_id=user.id, resource_id=statement.id, user_agent=ua)

    # Return file with appropriate content type
    content_type = 'text/csv' if statement.file_name.endswith('.csv') else 'application/pdf'
    return file_bytes, 200, {
        'Content-Disposition': f'attachment; filename="{statement.file_name}"',
        'Content-Type': content_type,
    }

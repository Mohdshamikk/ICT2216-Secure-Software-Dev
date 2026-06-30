from __future__ import annotations

import io

from flask import Blueprint, current_app, jsonify, request

from app.middleware.auth import require_auth

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


def _upload_statement_file(uploaded_file):
	return jsonify({'message': 'Upload accepted'}), 200


@statements_bp.post('/upload')
@require_auth
def upload_statement():
	uploaded_file = request.files.get('file')

	if uploaded_file is None or uploaded_file.filename == '':
		return jsonify({'error': 'file is required'}), 400

	max_upload_size_bytes = current_app.config['MAX_UPLOAD_SIZE_MB'] * 1024 * 1024
	if _uploaded_file_size_bytes(uploaded_file) > max_upload_size_bytes:
		return jsonify({'error': 'File too large'}), 413

	return _upload_statement_file(uploaded_file)

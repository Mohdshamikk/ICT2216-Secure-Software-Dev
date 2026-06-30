from __future__ import annotations

import csv
import io
from pathlib import Path

import magic
from uuid import uuid4

from flask import Blueprint, current_app, jsonify, request

from app.middleware.auth import require_auth
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


def _storage_base_path() -> Path:
	base_path = Path(current_app.config['STORAGE_BASE_PATH']).expanduser().resolve()
	static_path = Path(current_app.static_folder).expanduser().resolve()

	if base_path == static_path or static_path in base_path.parents:
		raise ValueError('STORAGE_BASE_PATH must be outside the Flask static directory')

	return base_path


def _statement_storage_path(original_filename: str) -> Path:
	storage_filename = _server_generated_filename(original_filename)
	return _storage_base_path() / storage_filename


def _uploaded_file_bytes(uploaded_file) -> bytes:
	stream = uploaded_file.stream
	current_position = stream.tell()
	stream.seek(0)
	file_bytes = stream.read()
	stream.seek(current_position)
	return file_bytes


def _statement_upload_metadata(uploaded_file) -> dict[str, object]:
	storage_path = _statement_storage_path(uploaded_file.filename)
	file_bytes = _uploaded_file_bytes(uploaded_file)
	file_hash = hash_file_sha256(file_bytes)
	return {
		'storage_path': storage_path,
		'file_hash': file_hash,
		'file_bytes': file_bytes,
	}


def _upload_statement_file(uploaded_file):
	metadata = _statement_upload_metadata(uploaded_file)
	_ = metadata['storage_path']
	_ = metadata['file_hash']
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

	mime_type = _uploaded_file_mime_type(uploaded_file)
	if mime_type not in {'text/csv', 'application/pdf'}:
		return jsonify({'error': 'Unsupported file type'}), 415

	return _upload_statement_file(uploaded_file)

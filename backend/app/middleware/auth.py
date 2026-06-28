from __future__ import annotations

import hashlib
from datetime import datetime, timedelta
from functools import wraps

from flask import g, jsonify, request

from app.extensions import db
from app.models import Session

_IDLE_TIMEOUT_MINUTES = 15


def require_auth(f):
    """Validate session cookie, enforce idle timeout, and bind g.current_user + g.session."""
    @wraps(f)
    def decorated(*args, **kwargs):
        raw_token = request.cookies.get('session_token')
        if not raw_token:
            return jsonify({'error': 'Authentication required'}), 401

        token_hash = hashlib.sha256(raw_token.encode()).hexdigest()
        session = Session.query.filter_by(token_hash=token_hash).first()

        if not session:
            return jsonify({'error': 'Invalid or expired session'}), 401

        now = datetime.utcnow()

        if session.expires_at < now:
            db.session.delete(session)
            db.session.commit()
            return jsonify({'error': 'Session expired'}), 401

        if now - session.last_active > timedelta(minutes=_IDLE_TIMEOUT_MINUTES):
            db.session.delete(session)
            db.session.commit()
            return jsonify({'error': 'Session timed out due to inactivity'}), 401

        session.last_active = now
        db.session.commit()

        g.current_user = session.user
        g.session = session
        return f(*args, **kwargs)

    return decorated

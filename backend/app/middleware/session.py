from datetime import datetime, timezone, timedelta
from functools import wraps
from flask import request, jsonify, g
from app.extensions import db
from app.models import Session

SESSION_IDLE_MINUTES = 15


def validate_session(session_id):
    now = datetime.now(timezone.utc)
    session = Session.query.filter_by(id=session_id).first()

    if not session:
        return None

    # Check absolute timeout (8 hours)
    if session.expires_at.replace(tzinfo=timezone.utc) < now:
        db.session.delete(session)
        db.session.commit()
        return None

    # Check idle timeout (15 minutes)
    last_active = session.last_active.replace(tzinfo=timezone.utc)
    if (now - last_active) > timedelta(minutes=SESSION_IDLE_MINUTES):
        db.session.delete(session)
        db.session.commit()
        return None

    # Update last active
    session.last_active = now
    db.session.commit()
    return session


def session_middleware(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        session_id = request.cookies.get('session_id')
        if not session_id:
            return jsonify({'error': 'Unauthorized'}), 401

        session = validate_session(session_id)
        if not session:
            return jsonify({'error': 'Session expired'}), 401

        g.session = session
        return f(*args, **kwargs)
    return decorated
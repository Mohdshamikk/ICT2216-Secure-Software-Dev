from datetime import datetime, timezone, timedelta
from app.extensions import db
from app.models import User

LOCKOUT_MAX_ATTEMPTS = 5
LOCKOUT_DURATION_MINUTES = 10


def check_lockout(user):
    if user.locked_until is None:
        return False
    
    now = datetime.now(timezone.utc)
    locked_until = user.locked_until.replace(tzinfo=timezone.utc)
    
    if locked_until > now:
        return True  # still locked
    
    # Lockout expired, clear it
    user.locked_until = None
    user.failed_login_attempts = 0
    db.session.commit()
    return False


def record_failed_attempt(user):
    user.failed_login_attempts = (user.failed_login_attempts or 0) + 1
    
    if user.failed_login_attempts >= LOCKOUT_MAX_ATTEMPTS:
        user.locked_until = datetime.now(timezone.utc) + timedelta(minutes=LOCKOUT_DURATION_MINUTES)
    
    db.session.commit()


def clear_lockout(user):
    user.failed_login_attempts = 0
    user.locked_until = None
    db.session.commit()
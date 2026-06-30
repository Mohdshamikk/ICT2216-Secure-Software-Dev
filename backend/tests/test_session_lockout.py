from datetime import datetime, timezone, timedelta
from unittest.mock import MagicMock, patch

from app.utils.lockout import (
    LOCKOUT_MAX_ATTEMPTS,
    LOCKOUT_DURATION_MINUTES,
    check_lockout,
    record_failed_attempt,
    clear_lockout,
)


# ============================================================================
# Lockout Tests (SR-07)
# ============================================================================

@patch('app.utils.lockout.db')
def test_check_lockout_returns_false_when_not_locked(mock_db):
    user = MagicMock()
    user.locked_until = None

    result = check_lockout(user)

    assert result is False


@patch('app.utils.lockout.db')
def test_check_lockout_returns_true_when_still_locked(mock_db):
    user = MagicMock()
    user.locked_until = datetime.now(timezone.utc) + timedelta(minutes=5)

    result = check_lockout(user)

    assert result is True


@patch('app.utils.lockout.db')
def test_check_lockout_clears_expired_lock(mock_db):
    user = MagicMock()
    user.locked_until = datetime.now(timezone.utc) - timedelta(minutes=1)
    user.failed_login_attempts = 5

    result = check_lockout(user)

    assert result is False
    assert user.locked_until is None
    assert user.failed_login_attempts == 0


@patch('app.utils.lockout.db')
def test_record_failed_attempt_increments_counter(mock_db):
    user = MagicMock()
    user.failed_login_attempts = 0
    user.locked_until = None

    record_failed_attempt(user)

    assert user.failed_login_attempts == 1
    assert user.locked_until is None


@patch('app.utils.lockout.db')
def test_record_failed_attempt_locks_account_at_max_attempts(mock_db):
    user = MagicMock()
    user.failed_login_attempts = LOCKOUT_MAX_ATTEMPTS - 1
    user.locked_until = None

    record_failed_attempt(user)

    assert user.failed_login_attempts == LOCKOUT_MAX_ATTEMPTS
    assert user.locked_until is not None
    assert user.locked_until > datetime.now(timezone.utc)


@patch('app.utils.lockout.db')
def test_clear_lockout_resets_user(mock_db):
    user = MagicMock()
    user.failed_login_attempts = 5
    user.locked_until = datetime.now(timezone.utc) + timedelta(minutes=10)

    clear_lockout(user)

    assert user.failed_login_attempts == 0
    assert user.locked_until is None


# ============================================================================
# Session Middleware Tests (SR-17 / SR-18)
# ============================================================================

@patch('app.middleware.session.db')
@patch('app.middleware.session.Session')
def test_validate_session_returns_none_for_missing_session(mock_session_model, mock_db):
    from app.middleware.session import validate_session

    mock_session_model.query.filter_by.return_value.first.return_value = None

    result = validate_session('fake-id')

    assert result is None


@patch('app.middleware.session.db')
@patch('app.middleware.session.Session')
def test_validate_session_deletes_expired_absolute_timeout(mock_session_model, mock_db):
    from app.middleware.session import validate_session

    mock_session = MagicMock()
    mock_session.expires_at = datetime.now(timezone.utc) - timedelta(hours=1)
    mock_session_model.query.filter_by.return_value.first.return_value = mock_session

    result = validate_session('fake-id')

    assert result is None
    mock_db.session.delete.assert_called_once_with(mock_session)


@patch('app.middleware.session.db')
@patch('app.middleware.session.Session')
def test_validate_session_deletes_expired_idle_timeout(mock_session_model, mock_db):
    from app.middleware.session import validate_session

    mock_session = MagicMock()
    mock_session.expires_at = datetime.now(timezone.utc) + timedelta(hours=1)
    mock_session.last_active = datetime.now(timezone.utc) - timedelta(minutes=20)
    mock_session_model.query.filter_by.return_value.first.return_value = mock_session

    result = validate_session('fake-id')

    assert result is None
    mock_db.session.delete.assert_called_once_with(mock_session)


@patch('app.middleware.session.db')
@patch('app.middleware.session.Session')
def test_validate_session_returns_session_when_valid(mock_session_model, mock_db):
    from app.middleware.session import validate_session

    mock_session = MagicMock()
    mock_session.expires_at = datetime.now(timezone.utc) + timedelta(hours=1)
    mock_session.last_active = datetime.now(timezone.utc) - timedelta(minutes=5)
    mock_session_model.query.filter_by.return_value.first.return_value = mock_session

    result = validate_session('fake-id')

    assert result is mock_session


# ============================================================================
# Auth Middleware Integration Test (SR-18)
# ============================================================================

def test_require_auth_rejects_missing_cookie():
    from app import create_app
    app = create_app('development')
    client = app.test_client()

    r = client.get('/api/auth/me')
    assert r.status_code == 401
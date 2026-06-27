from flask import Blueprint

auth_bp = Blueprint('auth', __name__, url_prefix='/api/auth')

# FR-01: POST /api/auth/login (step 1)
# FR-01: POST /api/auth/login/mfa (step 2)
# FR-01: POST /api/auth/logout
# FR-01: GET  /api/auth/me
# FR-01: POST /api/auth/mfa/setup
# FR-01: POST /api/auth/mfa/enable
# FR-01: POST /api/auth/mfa/disable
# FR-02: POST /api/auth/register
# FR-02: GET  /api/auth/verify-email
# FR-14: POST /api/auth/password-reset/request
# FR-14: POST /api/auth/password-reset/confirm

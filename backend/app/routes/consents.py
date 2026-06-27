from flask import Blueprint

consents_bp = Blueprint('consents', __name__, url_prefix='/api')

# FR-09: POST   /api/consents/household
# FR-09: DELETE /api/consents/household/:id
# FR-10: POST   /api/consents/advisor
# FR-10: DELETE /api/consents/advisor/:id
# FR-15: GET    /api/household/summary
# FR-16: GET    /api/advisor/clients
# FR-16: GET    /api/advisor/clients/:grantor_id/analytics

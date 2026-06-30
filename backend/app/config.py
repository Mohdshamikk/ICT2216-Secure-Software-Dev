import os
from sqlalchemy.engine import URL
from dotenv import load_dotenv

load_dotenv()


def _build_db_url():
    raw = os.getenv('DATABASE_URL')
    if raw:
        return raw
    return URL.create(
        drivername='postgresql+psycopg2',
        username=os.getenv('DB_USER'),
        password=os.getenv('DB_PASSWORD'),
        host=os.getenv('DB_HOST'),
        port=int(os.getenv('DB_PORT', 5432)),
        database=os.getenv('DB_NAME', 'postgres'),
    )


class Config:
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key')
    SQLALCHEMY_DATABASE_URI = _build_db_url()
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_pre_ping': True,
        'pool_recycle': 280,
        'pool_size': 5,
        'max_overflow': 10,
    }
    ENCRYPTION_KEY = os.getenv('ENCRYPTION_KEY')
    FRONTEND_URL = os.getenv('FRONTEND_URL', 'http://localhost:5173')
    MAIL_SERVER = os.getenv('MAIL_SERVER')
    MAIL_USERNAME = os.getenv('MAIL_USERNAME')
    MAIL_PASSWORD = os.getenv('MAIL_PASSWORD')
    MFA_ISSUER = os.getenv('MFA_ISSUER', 'FinTrack')
    MAX_UPLOAD_SIZE_MB = int(os.getenv('MAX_UPLOAD_SIZE_MB', 10))
    STORAGE_BASE_PATH = os.getenv('STORAGE_BASE_PATH')
    ALLOWED_EXTENSIONS = set(os.getenv('ALLOWED_EXTENSIONS', 'pdf,csv').split(','))
    # Reject oversized request bodies before they are buffered (existing 413 handler formats the response)
    MAX_CONTENT_LENGTH = int(os.getenv('MAX_UPLOAD_SIZE_MB', 10)) * 1024 * 1024

    # Supabase Storage — raw bank-statement files live in a private bucket
    SUPABASE_URL = os.getenv('SUPABASE_URL')
    SUPABASE_SERVICE_KEY = os.getenv('SUPABASE_SERVICE_KEY')
    SUPABASE_BUCKET = os.getenv('SUPABASE_BUCKET', 'bank-statements')


class DevelopmentConfig(Config):
    DEBUG = True
    SQLALCHEMY_ECHO = False


class ProductionConfig(Config):
    DEBUG = False

    def __init__(self):
        if not os.getenv('SECRET_KEY'):
            raise RuntimeError('SECRET_KEY must be set in production')
        if not os.getenv('ENCRYPTION_KEY'):
            raise RuntimeError('ENCRYPTION_KEY must be set in production')


config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig,
}

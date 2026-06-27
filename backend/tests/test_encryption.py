import base64
import importlib


def _load_module(monkeypatch):
    monkeypatch.setenv('ENCRYPTION_KEY', base64.b64encode(b'0' * 32).decode('ascii'))
    module = importlib.import_module('app.utils.encryption')
    module._get_encryption_key.cache_clear()
    return module


def test_encrypt_and_decrypt_round_trip(monkeypatch):
    encryption = _load_module(monkeypatch)

    ciphertext = encryption.encrypt_field('sensitive-value')

    assert isinstance(ciphertext, str)
    assert encryption.decrypt_field(ciphertext) == 'sensitive-value'


def test_encrypt_field_requires_string(monkeypatch):
    encryption = _load_module(monkeypatch)

    try:
        encryption.encrypt_field(123)
    except TypeError as exc:
        assert 'plaintext must be a string' in str(exc)
    else:
        raise AssertionError('TypeError was not raised')

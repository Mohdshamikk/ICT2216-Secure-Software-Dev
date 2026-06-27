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


def test_hash_file_sha256_known_answer(monkeypatch):
    encryption = _load_module(monkeypatch)

    assert encryption.hash_file_sha256(b'abc') == (
        'ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad'
    )


def test_hash_file_sha256_requires_bytes_like(monkeypatch):
    encryption = _load_module(monkeypatch)

    try:
        encryption.hash_file_sha256('abc')
    except TypeError as exc:
        assert 'file_bytes must be bytes-like' in str(exc)
    else:
        raise AssertionError('TypeError was not raised')

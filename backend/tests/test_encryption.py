from app.core.encryption import decrypt_value, encrypt_value, mask_secret


def test_encrypt_decrypt_roundtrip():
    plaintext = "upstox-api-key-abc123xyz"
    ciphertext = encrypt_value(plaintext)

    assert ciphertext != plaintext
    assert decrypt_value(ciphertext) == plaintext


def test_decrypt_garbage_returns_none_not_an_exception():
    assert decrypt_value("not-a-real-token") is None


def test_mask_secret_never_reveals_the_middle():
    masked = mask_secret("sk-abcdefgh12345678wxyz")
    assert masked.startswith("sk-a")
    assert masked.endswith("wxyz")
    assert "abcdefgh12345678" not in masked

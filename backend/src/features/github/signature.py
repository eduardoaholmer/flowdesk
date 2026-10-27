import hashlib
import hmac

_SIGNATURE_PREFIX = "sha256="


def is_valid_webhook_signature(secret: str, body: bytes, signature_header: str | None) -> bool:
    """Confere `X-Hub-Signature-256` (`sha256=<hex>`) contra o HMAC-SHA256 do corpo
    bruto, em tempo constante. O corpo precisa ser exatamente os bytes recebidos:
    qualquer reserialização do JSON muda o HMAC."""
    if not signature_header or not signature_header.startswith(_SIGNATURE_PREFIX):
        return False
    expected = hmac.new(secret.encode("utf-8"), body, hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected, signature_header.removeprefix(_SIGNATURE_PREFIX))

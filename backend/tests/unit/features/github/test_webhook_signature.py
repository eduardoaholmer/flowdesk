import pytest
from src.features.github.signature import is_valid_webhook_signature

from tests.github_payloads import sign

_SECRET = "webhook-secret"
_BODY = b'{"action":"deleted"}'


def test_signature_of_the_exact_body_is_valid() -> None:
    assert is_valid_webhook_signature(_SECRET, _BODY, sign(_SECRET, _BODY))


@pytest.mark.parametrize(
    "header",
    [
        None,
        "",
        sign("another-secret", _BODY),
        sign(_SECRET, _BODY).removeprefix("sha256="),
        "sha1=" + sign(_SECRET, _BODY).removeprefix("sha256="),
        sign(_SECRET, b'{"action": "deleted"}'),
    ],
    ids=["missing", "empty", "wrong-secret", "no-prefix", "sha1-prefix", "reserialized-body"],
)
def test_anything_but_the_exact_hmac_is_rejected(header: str | None) -> None:
    assert not is_valid_webhook_signature(_SECRET, _BODY, header)

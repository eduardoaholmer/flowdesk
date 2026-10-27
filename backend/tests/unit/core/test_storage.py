import pytest
from src.core.storage import build_storage_key


@pytest.mark.parametrize(
    ("suggested_name", "expected_suffix"),
    [
        ("print.png", "print.png"),
        ("../../etc/passwd", "passwd"),
        ("a/b.png", "b.png"),
        ("C:\\Users\\ada\\relatório final.pdf", "relat_rio_final.pdf"),
        ("..", ".."),
        ("", "arquivo"),
    ],
)
def test_build_storage_key_keeps_only_a_safe_basename(
    suggested_name: str, expected_suffix: str
) -> None:
    key = build_storage_key(suggested_name)

    prefix, suffix = key.split("-", 1)
    assert len(prefix) == 32
    assert suffix == expected_suffix
    assert "/" not in key

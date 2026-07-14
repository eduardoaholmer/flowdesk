import re

_HEX_COLOR_RE = re.compile(r"^#(?:[0-9A-Fa-f]{3}|[0-9A-Fa-f]{6})$")


def validate_hex_color(value: str) -> str:
    """Extraído de `features/projects/schemas.py` (Sprint 6) para `core/` porque
    Labels (Sprint 8) precisa exatamente da mesma validação — mesmo racional já
    aplicado a `core/slug.py::validate_slug_format` (`CLAUDE.md` §1).
    """
    if not _HEX_COLOR_RE.match(value):
        raise ValueError("A cor deve ser um código hexadecimal válido (ex.: #4F46E5).")
    return value

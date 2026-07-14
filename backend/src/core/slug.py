import re
import secrets
import unicodedata

SLUG_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
SLUG_MIN_LENGTH = 3
SLUG_MAX_LENGTH = 50


def slugify(name: str) -> str:
    """Melhor esforço de transliteração (`unicodedata`, sem dependência externa
    tipo `python-slugify`) — não precisa ser perfeito para todo alfabeto, só
    determinístico o bastante para reduzir colisão antes do fallback de sufixo.

    Extraído de `features/workspaces/service.py` (Sprint 5) para `core/` porque
    Projects (Sprint 6) precisa exatamente da mesma lógica — duplicar esta
    função por feature é o tipo de repetição que `CLAUDE.md` §1 pede para evitar.
    """
    normalized = unicodedata.normalize("NFKD", name).encode("ascii", "ignore").decode("ascii")
    slug = re.sub(r"[^a-z0-9]+", "-", normalized.lower()).strip("-")
    slug = re.sub(r"-{2,}", "-", slug)
    if len(slug) < SLUG_MIN_LENGTH:
        slug = f"{slug}-{secrets.token_hex(3)}" if slug else secrets.token_hex(4)
    return slug[:SLUG_MAX_LENGTH].strip("-")


def validate_slug_format(value: str) -> str:
    if not (SLUG_MIN_LENGTH <= len(value) <= SLUG_MAX_LENGTH):
        raise ValueError(f"O slug deve ter entre {SLUG_MIN_LENGTH} e {SLUG_MAX_LENGTH} caracteres.")
    if not SLUG_RE.match(value):
        raise ValueError(
            "O slug deve conter apenas letras minúsculas, números e hífens "
            "(sem hífen no início/fim ou repetido)."
        )
    return value

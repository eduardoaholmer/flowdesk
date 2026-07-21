import re
import secrets
import string
import unicodedata

KEY_RE = re.compile(r"^[A-Z]{2,4}$")
KEY_MIN_LENGTH = 2
KEY_MAX_LENGTH = 4

_WORD_RE = re.compile(r"[A-Za-z]+")


def derive_project_key(name: str) -> str:
    """Deriva uma key curta (2-4 letras maiúsculas) a partir do nome, no mesmo
    espírito de `core/slug.py::slugify`: melhor esforço determinístico o
    bastante para reduzir colisão antes do fallback aleatório do service.

    Nome com múltiplas palavras vira as iniciais (`"Public Roadmap"` -> `"PR"`);
    uma só palavra vira o prefixo (`"Palette"` -> `"PAL"`). Puramente decorativa
    — não tem relação com o identificador `FD-{n}` de uma Issue (ADR-012).
    """
    normalized = unicodedata.normalize("NFKD", name).encode("ascii", "ignore").decode("ascii")
    words = _WORD_RE.findall(normalized)
    if len(words) >= KEY_MIN_LENGTH:
        candidate = "".join(word[0] for word in words)[:KEY_MAX_LENGTH].upper()
    elif words:
        candidate = words[0][:3].upper()
    else:
        candidate = ""
    while len(candidate) < KEY_MIN_LENGTH:
        candidate += secrets.choice(string.ascii_uppercase)
    return candidate


def random_project_key() -> str:
    return "".join(secrets.choice(string.ascii_uppercase) for _ in range(KEY_MAX_LENGTH))


def validate_project_key_format(value: str) -> str:
    normalized = value.strip().upper()
    if not KEY_RE.match(normalized):
        raise ValueError(
            f"A key deve ter entre {KEY_MIN_LENGTH} e {KEY_MAX_LENGTH} letras "
            "maiúsculas (sem espaços, números ou símbolos)."
        )
    return normalized

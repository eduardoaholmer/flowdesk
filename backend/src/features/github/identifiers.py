import re
from collections.abc import Iterable

from src.features.issues.models import ISSUE_IDENTIFIER_PREFIX

# `FD-123` sem diferenciar maiúsculas, com fronteira dos dois lados: `FD-12` não casa
# dentro de `FD-123` nem de `XFD-12`. Até 9 dígitos porque `issues.number` é
# `INTEGER` — um número maior nunca seria de uma issue e quebraria a consulta.
_IDENTIFIER_RE = re.compile(
    rf"(?<![A-Za-z0-9]){re.escape(ISSUE_IDENTIFIER_PREFIX)}-(\d{{1,9}})(?![A-Za-z0-9])",
    re.IGNORECASE,
)
# Um PR que cita mais issues que isso é um changelog ou uma lista, não um PR que
# resolve cada uma delas; o teto limita o trabalho por entrega.
MAX_ISSUE_REFERENCES = 50


def extract_issue_numbers(texts: Iterable[str | None]) -> list[int]:
    """Números das issues citadas, na ordem em que aparecem, sem repetição."""
    numbers: list[int] = []
    for text in texts:
        if not text:
            continue
        for match in _IDENTIFIER_RE.finditer(text):
            number = int(match.group(1))
            if number not in numbers:
                numbers.append(number)
                if len(numbers) == MAX_ISSUE_REFERENCES:
                    return numbers
    return numbers

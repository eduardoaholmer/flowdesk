import pytest
from src.features.github.identifiers import MAX_ISSUE_REFERENCES, extract_issue_numbers


@pytest.mark.parametrize(
    ("texts", "expected"),
    [
        (["fd-123-corrige-login"], [123]),
        (["feature/FD-7"], [7]),
        (["Fix Fd-42 no checkout"], [42]),
        (["Closes FD-12, FD-3 e (FD-5)."], [12, 3, 5]),
        (["FD-0042"], [42]),
    ],
    ids=["branch", "branch-with-folder", "mixed-case", "several-in-text", "leading-zeros"],
)
def test_identifiers_are_found_in_branch_title_and_body(
    texts: list[str], expected: list[int]
) -> None:
    assert extract_issue_numbers(texts) == expected


def test_word_boundaries_avoid_partial_matches() -> None:
    """`FD-12` não pode casar dentro de `FD-123`, nem `XFD-9`/`FD-9a` contar."""
    assert extract_issue_numbers(["FD-123", "XFD-9 FD-9a fd-9_"]) == [123, 9]


def test_repeated_identifiers_count_once_in_order_of_appearance() -> None:
    assert extract_issue_numbers(["fd-2-x", "FD-1 e FD-2", None, "", "FD-1"]) == [2, 1]


def test_numbers_beyond_the_issue_number_column_are_ignored() -> None:
    assert extract_issue_numbers(["FD-1234567890 FD-123456789"]) == [123456789]


def test_text_without_identifier_yields_nothing() -> None:
    assert extract_issue_numbers(["Update README", "FD- 12", "FD12", None]) == []


def test_references_are_capped() -> None:
    body = " ".join(f"FD-{n}" for n in range(1, MAX_ISSUE_REFERENCES + 10))

    assert extract_issue_numbers([body]) == list(range(1, MAX_ISSUE_REFERENCES + 1))

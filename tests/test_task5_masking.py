"""Shared masker regression for complete Luhn candidates in escalation summaries."""

import pytest

from core.security import mask_pii


@pytest.mark.parametrize("number", ["4111 1111 1111 1111", "4111-1111-1111-1111", "4111111111111111",
                                    "5555 5555 5555 4444", "3782 822463 10005"])
def test_complete_payment_card_masked(number: str) -> None:
    output = mask_pii("contact caller@example.com card " + number + " order ORD-AbC-42")
    assert number not in output and "[MASKED_CARD]" in output and "ORD-AbC-42" in output


def test_partial_card_candidate_cannot_hide_full_card() -> None:
    assert mask_pii("4111 1111 1111 1111") == "[MASKED_CARD]"
    assert mask_pii("4111 1111 1111 1112") == "4111 1111 1111 1112"

"""Frozen evaluation text cannot become implementation examples or rules."""

from scripts.check_holdouts import check


def test_heldout_hashes_and_no_implementation_contamination():
    assert check()["implementation_contamination"] == []

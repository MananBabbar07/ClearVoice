import pytest

from scripts.sample_pubhealth import filter_rows, map_label, sample_stratified


def test_map_label_valid_and_invalid():
    assert map_label(0) == ("FALSE", "false", "false")
    assert map_label(1) == ("MISLEADING", "misleading", "mixture")
    assert map_label(2) == ("TRUE", "true", "true")
    assert map_label(3) == ("INSUFFICIENT EVIDENCE", "insufficient", "unproven")

    assert map_label("false") == ("FALSE", "false", "false")
    assert map_label("mixture") == ("MISLEADING", "misleading", "mixture")
    assert map_label("true") == ("TRUE", "true", "true")
    assert map_label("unproven") == ("INSUFFICIENT EVIDENCE", "insufficient", "unproven")

    with pytest.raises(ValueError):
        map_label(-1)

    with pytest.raises(ValueError):
        map_label("-1")

    with pytest.raises(ValueError):
        map_label("unknown")


def test_filter_rows_with_inline_dataset():
    fake_rows = [
        {"claim": "Valid true claim", "label": 2, "explanation": "Fact check true"},
        {"claim": "  Valid false claim  ", "label": "false", "explanation": "Fact check false"},
        {"claim": "Valid mixture claim", "label": 1, "explanation": "Fact check mixture"},
        {"claim": "Valid unproven claim", "label": 3, "explanation": "Fact check unproven"},
        {"claim": "", "label": 2, "explanation": "Empty claim"},
        {"claim": "   ", "label": 0, "explanation": "Whitespace only"},
        {"claim": "X" * 200, "label": 2, "explanation": "Too long claim"},
        {"claim": "Y" * 250, "label": 1, "explanation": "Way too long claim"},
        {"claim": "Unlabelled claim", "label": -1, "explanation": "Negative one label"},
        {"claim": "String negative one", "label": "-1", "explanation": "String neg one"},
        {"claim": "Invalid label value", "label": 99, "explanation": "Bad label"},
        {"claim": "valid true claim", "label": 2, "explanation": "Duplicate lowercase"},
    ]

    by_class, stats = filter_rows(fake_rows)

    assert stats["total"] == 12
    assert stats["kept"] == 4
    assert stats["dropped_empty"] == 2
    assert stats["dropped_len_ge_200"] == 2
    assert stats["dropped_label_invalid"] == 3
    assert stats["dropped_duplicate"] == 1

    assert len(by_class["true"]) == 1
    assert len(by_class["false"]) == 1
    assert len(by_class["misleading"]) == 1
    assert len(by_class["insufficient"]) == 1

    true_item = by_class["true"][0]
    assert true_item["claim"] == "Valid true claim"
    assert true_item["expected"] == "TRUE"
    assert true_item["category"] == "true"
    assert true_item["source"] == "PUBHEALTH"
    assert true_item["original_label"] == "true"
    assert true_item["explanation"] == "Fact check true"


def test_sample_stratified_deterministic_and_bounded():
    by_class = {
        "true": [{"claim": f"T{i}", "category": "true"} for i in range(20)],
        "false": [{"claim": f"F{i}", "category": "false"} for i in range(5)],
        "misleading": [{"claim": f"M{i}", "category": "misleading"} for i in range(15)],
        "insufficient": [{"claim": f"I{i}", "category": "insufficient"} for i in range(14)],
    }

    sample1, counts1 = sample_stratified(by_class, n_per_class=10, seed=42)
    sample2, counts2 = sample_stratified(by_class, n_per_class=10, seed=42)

    assert sample1 == sample2
    assert counts1["true"] == 10
    assert counts1["false"] == 5
    assert counts1["misleading"] == 10
    assert counts1["insufficient"] == 10
    assert len(sample1) == 35

    ids = [item["id"] for item in sample1]
    assert ids == list(range(1, 36))

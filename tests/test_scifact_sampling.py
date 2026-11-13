from scripts.sample_scifact import (
    filter_scifact_records,
    map_claim_labels,
    sample_stratified_scifact,
)


def test_map_claim_labels():
    assert map_claim_labels({"SUPPORT"}) == ("TRUE", "true")
    assert map_claim_labels({"support"}) == ("TRUE", "true")
    assert map_claim_labels({"CONTRADICT"}) == ("FALSE", "false")
    assert map_claim_labels({"contradict"}) == ("FALSE", "false")
    assert map_claim_labels(set()) == ("INSUFFICIENT EVIDENCE", "insufficient")
    assert map_claim_labels({""}) == ("INSUFFICIENT EVIDENCE", "insufficient")
    assert map_claim_labels({"SUPPORT", "CONTRADICT"}) is None
    assert map_claim_labels({"UNKNOWN"}) is None


def test_filter_scifact_records_inline():
    fake_records = [
        {"id": 1, "claim": "Vitamin D improves bone health.", "evidence_label": "SUPPORT"},
        {"id": 1, "claim": "Vitamin D improves bone health.", "evidence_label": "SUPPORT"},
        {"id": 2, "claim": "Smoking decreases cancer risk.", "evidence_label": "CONTRADICT"},
        {"id": 3, "claim": "Unstudied protein interaction.", "evidence_label": ""},
        {"id": 4, "claim": "Conflicting findings claim.", "evidence_label": "SUPPORT"},
        {"id": 4, "claim": "Conflicting findings claim.", "evidence_label": "CONTRADICT"},
        {"id": 5, "claim": "", "evidence_label": "SUPPORT"},
        {"id": 6, "claim": "   ", "evidence_label": ""},
        {"id": 7, "claim": "Z" * 200, "evidence_label": "SUPPORT"},
        {"id": 8, "claim": "vitamin d improves bone health.", "evidence_label": "SUPPORT"},
    ]

    by_class, stats = filter_scifact_records(fake_records)

    assert stats["total_claims"] == 8
    assert stats["kept"] == 3
    assert stats["dropped_empty"] == 2
    assert stats["dropped_len_ge_200"] == 1
    assert stats["dropped_conflicting"] == 1
    assert stats["dropped_duplicate"] == 1

    assert len(by_class["true"]) == 1
    assert len(by_class["false"]) == 1
    assert len(by_class["insufficient"]) == 1

    true_item = by_class["true"][0]
    assert true_item["claim"] == "Vitamin D improves bone health."
    assert true_item["expected"] == "TRUE"
    assert true_item["category"] == "true"
    assert true_item["source"] == "SciFact"
    assert true_item["scifact_id"] == 1


def test_sample_stratified_scifact():
    by_class = {
        "true": [{"claim": f"T{i}", "category": "true"} for i in range(25)],
        "false": [{"claim": f"F{i}", "category": "false"} for i in range(8)],
        "insufficient": [{"claim": f"I{i}", "category": "insufficient"} for i in range(30)],
    }

    sample1, counts1 = sample_stratified_scifact(by_class, n_per_class=10, seed=42)
    sample2, counts2 = sample_stratified_scifact(by_class, n_per_class=10, seed=42)

    assert sample1 == sample2
    assert counts1["true"] == 10
    assert counts1["false"] == 8
    assert counts1["insufficient"] == 10
    assert len(sample1) == 28

    ids = [item["id"] for item in sample1]
    assert ids == list(range(1, 29))


import json
import os
import random
from typing import Optional


def map_claim_labels(labels: set[str]) -> Optional[tuple[str, str]]:
    cleaned = {str(lbl).strip().upper() for lbl in labels if str(lbl).strip()}
    if "SUPPORT" in cleaned and "CONTRADICT" in cleaned:
        return None
    if "SUPPORT" in cleaned:
        return ("TRUE", "true")
    if "CONTRADICT" in cleaned:
        return ("FALSE", "false")
    if len(cleaned) == 0:
        return ("INSUFFICIENT EVIDENCE", "insufficient")
    return None


def filter_scifact_records(records: list[dict]) -> tuple[dict[str, list[dict]], dict[str, int]]:
    claims_by_id: dict[object, dict] = {}
    for r in records:
        cid = r.get("id")
        claim_text = str(r.get("claim") or "").strip()
        ev_label = str(r.get("evidence_label") or "").strip().upper()

        if cid not in claims_by_id:
            claims_by_id[cid] = {
                "id": cid,
                "claim": claim_text,
                "labels": set(),
                "cited_doc_ids": r.get("cited_doc_ids"),
            }
        if ev_label:
            claims_by_id[cid]["labels"].add(ev_label)

    by_class: dict[str, list[dict]] = {
        "true": [],
        "false": [],
        "insufficient": [],
    }
    stats = {
        "total_claims": len(claims_by_id),
        "kept": 0,
        "dropped_len_ge_200": 0,
        "dropped_empty": 0,
        "dropped_conflicting": 0,
        "dropped_duplicate": 0,
    }
    seen_claims: set[str] = set()

    for item in claims_by_id.values():
        claim = item["claim"]
        if not claim:
            stats["dropped_empty"] += 1
            continue

        if len(claim) >= 200:
            stats["dropped_len_ge_200"] += 1
            continue

        claim_key = claim.lower()
        if claim_key in seen_claims:
            stats["dropped_duplicate"] += 1
            continue
        seen_claims.add(claim_key)

        mapped = map_claim_labels(item["labels"])
        if mapped is None:
            stats["dropped_conflicting"] += 1
            continue

        expected, category = mapped
        by_class[category].append({
            "claim": claim,
            "expected": expected,
            "category": category,
            "source": "SciFact",
            "scifact_id": item["id"],
        })
        stats["kept"] += 1

    return by_class, stats


def sample_stratified_scifact(
    by_class: dict[str, list[dict]],
    n_per_class: int = 20,
    seed: int = 42,
) -> tuple[list[dict], dict[str, int]]:
    rng = random.Random(seed)
    sampled: list[dict] = []
    class_counts: dict[str, int] = {}

    for category in ["true", "false", "insufficient"]:
        pool = by_class.get(category, [])
        count = min(len(pool), n_per_class)
        class_counts[category] = count
        if count < n_per_class:
            print(f"Warning: category '{category}' only has {count} claims (requested {n_per_class})")

        chosen = rng.sample(pool, count) if count < len(pool) else list(pool)
        sampled.extend(chosen)

    rng.shuffle(sampled)
    for idx, item in enumerate(sampled, start=1):
        item["id"] = idx

    return sampled, class_counts


def load_scifact_validation_records() -> tuple[list[dict], str]:
    try:
        import datasets

        ds = datasets.load_dataset("allenai/scifact", "claims", split="validation")
        return [dict(r) for r in ds], "datasets library (script)"
    except Exception as e_script:
        print(f"Direct script load did not work ({e_script}). Trying parquet conversion branch...")

    try:
        import pandas as pd

        parquet_url = (
            "https://huggingface.co/datasets/allenai/scifact/resolve/refs%2Fconvert%2Fparquet/claims/validation/0000.parquet"
        )
        df = pd.read_parquet(parquet_url)
        route_desc = "parquet conversion branch (refs/convert/parquet/claims/validation/0000.parquet)"
        return df.to_dict(orient="records"), route_desc
    except Exception as e_parquet:
        print(f"Parquet conversion branch failed: {e_parquet}")

    raise RuntimeError("Failed to load SciFact validation split via both script and parquet routes.")


def main() -> None:
    records, route = load_scifact_validation_records()
    print(f"SciFact loaded successfully via: {route}")
    print(f"Loaded {len(records)} raw rows.")

    by_class, stats = filter_scifact_records(records)
    print("\nDropped claim statistics:")
    for k, v in stats.items():
        print(f"  {k}: {v}")

    print("\nEligible unique claims per class before sampling:")
    for cat, items in by_class.items():
        print(f"  {cat}: {len(items)}")

    sampled, sampled_counts = sample_stratified_scifact(by_class, n_per_class=20, seed=42)
    print(f"\nSampled claims per class (total {len(sampled)}):")
    for cat, cnt in sampled_counts.items():
        print(f"  {cat}: {cnt}")

    root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    output_path = os.path.join(root_dir, "benchmark_scifact.json")
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(sampled, f, indent=2, ensure_ascii=False)

    print(f"\nWrote {len(sampled)} claims to {output_path}")


if __name__ == "__main__":
    main()

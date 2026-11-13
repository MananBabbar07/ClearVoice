import json
import os
import random

LABEL_MAP: dict[object, tuple[str, str, str]] = {
    0: ("FALSE", "false", "false"),
    1: ("MISLEADING", "misleading", "mixture"),
    2: ("TRUE", "true", "true"),
    3: ("INSUFFICIENT EVIDENCE", "insufficient", "unproven"),
    "false": ("FALSE", "false", "false"),
    "mixture": ("MISLEADING", "misleading", "mixture"),
    "true": ("TRUE", "true", "true"),
    "unproven": ("INSUFFICIENT EVIDENCE", "insufficient", "unproven"),
}


def map_label(label: object) -> tuple[str, str, str]:
    if label in (-1, "-1") or label not in LABEL_MAP:
        raise ValueError(f"Invalid label: {label}")
    return LABEL_MAP[label]


def filter_rows(rows: list[dict]) -> tuple[dict[str, list[dict]], dict[str, int]]:
    by_class: dict[str, list[dict]] = {
        "true": [],
        "false": [],
        "misleading": [],
        "insufficient": [],
    }
    stats: dict[str, int] = {
        "total": len(rows),
        "kept": 0,
        "dropped_empty": 0,
        "dropped_len_ge_200": 0,
        "dropped_label_invalid": 0,
        "dropped_duplicate": 0,
    }
    seen_claims = set()

    for row in rows:
        label = row.get("label")
        if label in (-1, "-1") or label not in LABEL_MAP:
            stats["dropped_label_invalid"] += 1
            continue

        raw_claim = row.get("claim")
        claim = str(raw_claim).strip() if raw_claim is not None else ""
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

        expected, category, orig_label = map_label(label)
        explanation = str(row.get("explanation") or "").strip()

        item = {
            "claim": claim,
            "expected": expected,
            "category": category,
            "source": "PUBHEALTH",
            "original_label": orig_label,
            "explanation": explanation,
        }
        by_class[category].append(item)
        stats["kept"] += 1

    return by_class, stats


def sample_stratified(
    by_class: dict[str, list[dict]],
    n_per_class: int = 14,
    seed: int = 42,
) -> tuple[list[dict], dict[str, int]]:
    rng = random.Random(seed)
    sampled: list[dict] = []
    class_counts: dict[str, int] = {}

    for category in ["true", "false", "misleading", "insufficient"]:
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


def load_pubhealth_test_split() -> tuple[list[dict], str]:
    route_used = ""
    try:
        import datasets

        ds = datasets.load_dataset("health_fact", split="test")
        route_used = "datasets library (script)"
        return [dict(r) for r in ds], route_used
    except Exception as e_script:
        print(f"Direct script load did not work ({e_script}). Trying parquet route...")

    try:
        import pandas as pd

        parquet_url = (
            "https://huggingface.co/datasets/health_fact/resolve/refs%2Fconvert%2Fparquet/default/test/0000.parquet"
        )
        df = pd.read_parquet(parquet_url)
        route_used = "parquet conversion branch (refs/convert/parquet)"
        return df.to_dict(orient="records"), route_used
    except Exception as e_parquet:
        print(f"Parquet conversion route failed: {e_parquet}")

    raise RuntimeError("Failed to load PUBHEALTH test split via both script and parquet routes.")


def main() -> None:
    rows, route = load_pubhealth_test_split()
    print(f"PUBHEALTH loaded successfully via: {route}")
    print(f"Loaded {len(rows)} raw rows from test split.")

    by_class, stats = filter_rows(rows)
    print("\nDropped row statistics:")
    for k, v in stats.items():
        print(f"  {k}: {v}")

    print("\nEligible claims per class before sampling:")
    for cat, items in by_class.items():
        print(f"  {cat}: {len(items)}")

    sampled, sampled_counts = sample_stratified(by_class, n_per_class=14, seed=42)
    print(f"\nSampled claims per class (total {len(sampled)}):")
    for cat, cnt in sampled_counts.items():
        print(f"  {cat}: {cnt}")

    root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    output_path = os.path.join(root_dir, "benchmark_pubhealth.json")
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(sampled, f, indent=2, ensure_ascii=False)

    print(f"\nWrote {len(sampled)} claims to {output_path}")


if __name__ == "__main__":
    main()

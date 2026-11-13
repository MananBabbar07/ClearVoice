import json
import math
import os
import sys
import time
from typing import Optional

import requests

VERDICT_LABELS = ["TRUE", "FALSE", "MISLEADING", "INSUFFICIENT EVIDENCE", "ERROR"]


def load_claims(path: str) -> list[dict]:
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def percentile(values: list[float], pct: float) -> float:
    if not values:
        return 0.0
    ordered = sorted(values)
    idx = (len(ordered) - 1) * (pct / 100.0)
    lower = math.floor(idx)
    upper = math.ceil(idx)
    if lower == upper:
        return round(ordered[int(idx)], 2)
    weight = idx - lower
    return round(ordered[lower] * (1.0 - weight) + ordered[upper] * weight, 2)


def verify_claim(
    claim: str,
    api_url: str,
    retries: int = 3,
    retry_delay: float = 5.0,
    timeout: float = 90.0,
) -> Optional[dict]:
    url = f"{api_url.rstrip('/')}/verify"
    for attempt in range(retries):
        try:
            response = requests.post(url, json={"claim": claim}, timeout=timeout)
            if response.status_code == 200:
                return response.json()
            print(f"  Attempt {attempt + 1} failed: status {response.status_code}")
        except Exception as e:
            print(f"  Attempt {attempt + 1} error: {e}")
        if attempt < retries - 1 and retry_delay > 0:
            time.sleep(retry_delay)
    print(f"  -> ERROR after {retries} attempts")
    return None


def compute_summary(results: list[dict], baseline_accuracy: float, api_url: str) -> dict:
    total = len(results)
    correct = sum(1 for r in results if r["correct"])
    errors = sum(1 for r in results if r["predicted"] == "ERROR")
    overall_accuracy = round((correct / total) * 100, 2) if total else 0.0

    per_category: dict[str, dict] = {}
    for row in results:
        cat = row["category"]
        entry = per_category.setdefault(cat, {"total": 0, "correct": 0, "accuracy": 0.0})
        entry["total"] += 1
        if row["correct"]:
            entry["correct"] += 1
    for entry in per_category.values():
        entry["accuracy"] = round((entry["correct"] / entry["total"]) * 100, 2) if entry["total"] else 0.0

    matrix: dict[str, dict[str, int]] = {
        expected: {pred: 0 for pred in VERDICT_LABELS}
        for expected in ["TRUE", "FALSE", "MISLEADING", "INSUFFICIENT EVIDENCE"]
    }
    for row in results:
        exp = row["expected"]
        pred = row["predicted"] if row["predicted"] in VERDICT_LABELS else "ERROR"
        if exp not in matrix:
            matrix[exp] = {label: 0 for label in VERDICT_LABELS}
        matrix[exp][pred] += 1

    latencies = [r["time_seconds"] for r in results]
    avg_latency = round(sum(latencies) / len(latencies), 2) if latencies else 0.0

    return {
        "api_url": api_url,
        "total": total,
        "correct": correct,
        "errors": errors,
        "overall_accuracy": overall_accuracy,
        "baseline_accuracy": baseline_accuracy,
        "per_category_accuracy": per_category,
        "confusion_matrix": matrix,
        "latency_seconds": {
            "avg": avg_latency,
            "p50": percentile(latencies, 50),
            "p95": percentile(latencies, 95),
        },
    }


def print_summary(summary: dict) -> None:
    print("\n=== BENCHMARK SUMMARY ===")
    print(f"Total claims     : {summary['total']}")
    print(f"Correct          : {summary['correct']}")
    print(f"Errors           : {summary['errors']}")
    print(f"Overall accuracy : {summary['overall_accuracy']}% (baseline: {summary['baseline_accuracy']}%)")
    lat = summary["latency_seconds"]
    print(f"Latency (s)      : avg={lat['avg']}s | p50={lat['p50']}s | p95={lat['p95']}s")

    print("\nPer-Category Accuracy:")
    for cat, stats in sorted(summary["per_category_accuracy"].items()):
        print(f"  {cat:<14}: {stats['correct']}/{stats['total']} ({stats['accuracy']}%)")

    print("\nConfusion Matrix (rows=expected, cols=predicted):")
    header = f"  {'EXPECTED':<22} " + " ".join(f"{label[:10]:>10}" for label in VERDICT_LABELS)
    print(header)
    for exp, counts in summary["confusion_matrix"].items():
        row_str = " ".join(f"{counts[label]:>10}" for label in VERDICT_LABELS)
        print(f"  {exp:<22} {row_str}")


def run_benchmark(
    claims_path: Optional[str] = None,
    output_path: Optional[str] = None,
    api_url: Optional[str] = None,
    baseline_accuracy: Optional[float] = None,
    delay: Optional[float] = None,
    retry_delay: Optional[float] = None,
    timeout: Optional[float] = None,
) -> dict:
    resolved_claims_path = (
        claims_path
        or os.getenv("CLAIMS_FILE")
        or os.getenv("BENCHMARK_CLAIMS_PATH", "benchmark_claims.json")
    )
    resolved_output_path = output_path or os.getenv("BENCHMARK_OUTPUT", "benchmark_results.json")
    resolved_api_url = api_url or os.getenv("API_URL", "http://localhost:8000")
    resolved_baseline = (
        float(baseline_accuracy)
        if baseline_accuracy is not None
        else float(os.getenv("BASELINE_ACCURACY", "0"))
    )
    resolved_delay = float(delay) if delay is not None else float(os.getenv("BENCHMARK_DELAY", "5"))
    resolved_retry_delay = (
        float(retry_delay)
        if retry_delay is not None
        else float(os.getenv("BENCHMARK_RETRY_DELAY", "5"))
    )
    resolved_timeout = float(timeout) if timeout is not None else float(os.getenv("BENCHMARK_TIMEOUT", "90"))

    claims = load_claims(resolved_claims_path)
    results: list[dict] = []

    for index, item in enumerate(claims):
        claim_text = item["claim"]
        expected = item["expected"]
        category = item["category"]
        print(f"[{index + 1}/{len(claims)}] Testing ({category}): {claim_text}")

        start = time.perf_counter()
        data = verify_claim(
            claim_text,
            api_url=resolved_api_url,
            retry_delay=resolved_retry_delay,
            timeout=resolved_timeout,
        )
        elapsed = round(time.perf_counter() - start, 2)

        if data is not None:
            predicted = data.get("verdict", "ERROR")
            papers = data.get("papers") or []
            top_sim = papers[0].get("similarity", 0.0) if papers and isinstance(papers[0], dict) else 0.0
            row = {
                "id": item.get("id", index + 1),
                "claim": claim_text,
                "category": category,
                "expected": expected,
                "predicted": predicted,
                "correct": predicted == expected,
                "confidence": data.get("confidence", 0.0),
                "top_similarity": top_sim,
                "time_seconds": elapsed,
                "cached": bool(data.get("cached", False)),
            }
            print(f"  -> {predicted} (expected {expected}, conf={row['confidence']}) in {elapsed}s")
        else:
            row = {
                "id": item.get("id", index + 1),
                "claim": claim_text,
                "category": category,
                "expected": expected,
                "predicted": "ERROR",
                "correct": False,
                "confidence": 0.0,
                "top_similarity": 0.0,
                "time_seconds": elapsed,
                "cached": False,
            }

        results.append(row)
        if index < len(claims) - 1 and resolved_delay > 0:
            time.sleep(resolved_delay)

    summary = compute_summary(results, resolved_baseline, resolved_api_url)
    payload = {"summary": summary, "results": results}

    with open(resolved_output_path, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2)
    print(f"\nSaved benchmark report to {resolved_output_path}")
    print_summary(summary)
    return payload


def main() -> int:
    payload = run_benchmark()
    summary = payload["summary"]
    if summary["overall_accuracy"] < summary["baseline_accuracy"]:
        print(
            f"\nFAIL: accuracy {summary['overall_accuracy']}% is below baseline {summary['baseline_accuracy']}%"
        )
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())

import requests
import time
import csv

API_URL = "https://manan77709-clearvoice-api.hf.space"

TEST_CLAIMS = [
    "antibiotics can cure the flu",
    "exercise reduces risk of heart disease",
    "smoking causes lung cancer",
    "vitamin C prevents colds",
    "vaccines cause autism",
    "obesity is linked to type 2 diabetes",
    "drinking bleach cures infections",
    "high blood pressure increases stroke risk",
    "sugar causes diabetes",
    "stress causes high blood pressure",
]

def run_benchmark():
    results = []

    for claim in TEST_CLAIMS:
        print(f"Testing: {claim}")
        start = time.time()

        response = requests.post(
            f"{API_URL}/verify",
            json={"claim": claim}
        )

        elapsed = round(time.time() - start, 2)
        data = response.json()

        results.append({
            "claim": claim,
            "verdict": data.get("verdict"),
            "confidence": data.get("confidence"),
            "top_similarity": data.get("papers", [{}])[0].get("similarity", 0),
            "time_seconds": elapsed,
            "cached": data.get("cached")
        })

        print(f"  → {data.get('verdict')} ({data.get('confidence')}) in {elapsed}s")
        time.sleep(1)

    return results


def save_results(results):
    with open("phase1_baseline.csv", "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=results[0].keys())
        writer.writeheader()
        writer.writerows(results)
    print("\nSaved to phase1_baseline.csv")


def print_summary(results):
    avg_confidence = round(sum(r["confidence"] for r in results) / len(results), 2)
    avg_similarity = round(sum(r["top_similarity"] for r in results) / len(results), 2)
    avg_time = round(sum(r["time_seconds"] for r in results) / len(results), 2)

    print("\n=== PHASE 1 BASELINE SUMMARY ===")
    print(f"Total claims tested : {len(results)}")
    print(f"Avg confidence      : {avg_confidence}")
    print(f"Avg top similarity  : {avg_similarity}")
    print(f"Avg response time   : {avg_time}s")


if __name__ == "__main__":
    results = run_benchmark()
    save_results(results)
    print_summary(results)
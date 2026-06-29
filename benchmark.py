import requests
import time
import csv

API_URL = "http://localhost:8000"

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

def verify_claim(claim, retries=3, delay=5):
    for attempt in range(retries):
        try:
            response = requests.post(
                f"{API_URL}/verify",
                json={"claim": claim},
                timeout=30
            )
            if response.status_code == 200:
                return response.json()
            else:
                print(f"  Attempt {attempt+1} failed: status {response.status_code}")
        except Exception as e:
            print(f"  Attempt {attempt+1} error: {e}")
        time.sleep(delay)
    return None

def run_benchmark():
    results = []
    for claim in TEST_CLAIMS:
        print(f"Testing: {claim}")
        start = time.time()

        data = verify_claim(claim)
        elapsed = round(time.time() - start, 2)

        if data:
            results.append({
                "claim": claim,
                "verdict": data.get("verdict"),
                "confidence": data.get("confidence"),
                "top_similarity": data.get("papers", [{}])[0].get("similarity", 0),
                "time_seconds": elapsed,
                "cached": data.get("cached")
            })
            print(f"  → {data.get('verdict')} ({data.get('confidence')}) in {elapsed}s")
        else:
            results.append({
                "claim": claim,
                "verdict": "ERROR",
                "confidence": 0.0,
                "top_similarity": 0.0,
                "time_seconds": elapsed,
                "cached": False
            })
            print(f"  → ERROR after {retries} attempts")

        time.sleep(3)  # wait 3 seconds between claims

    return results

def save_results(results):
    with open("phase1_baseline.csv", "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=results[0].keys())
        writer.writeheader()
        writer.writerows(results)
    print("\nSaved to phase1_baseline.csv")

def print_summary(results):
    valid = [r for r in results if r["verdict"] != "ERROR"]
    avg_confidence = round(sum(r["confidence"] for r in valid) / len(valid), 2)
    avg_similarity = round(sum(r["top_similarity"] for r in valid) / len(valid), 2)
    avg_time = round(sum(r["time_seconds"] for r in results) / len(results), 2)

    print("\n=== PHASE 1 BASELINE SUMMARY ===")
    print(f"Total claims tested : {len(results)}")
    print(f"Errors              : {len(results) - len(valid)}")
    print(f"Avg confidence      : {avg_confidence}")
    print(f"Avg top similarity  : {avg_similarity}")
    print(f"Avg response time   : {avg_time}s")

if __name__ == "__main__":
    results = run_benchmark()
    save_results(results)
    print_summary(results)
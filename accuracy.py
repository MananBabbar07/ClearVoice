import csv

# Ground truth labels — what the correct verdict should be
GROUND_TRUTH = {
    "antibiotics can cure the flu": "FALSE",
    "exercise reduces risk of heart disease": "TRUE",
    "smoking causes lung cancer": "TRUE",
    "vitamin C prevents colds": "MISLEADING",
    "vaccines cause autism": "FALSE",
    "obesity is linked to type 2 diabetes": "TRUE",
    "drinking bleach cures infections": "FALSE",
    "high blood pressure increases stroke risk": "TRUE",
    "sugar causes diabetes": "MISLEADING",
    "stress causes high blood pressure": "MISLEADING",
}

def calculate_accuracy():
    with open("phase1_baseline.csv", "r") as f:
        reader = csv.DictReader(f)
        results = list(reader)

    correct = 0
    print("\n=== ACCURACY BREAKDOWN ===")
    for r in results:
        expected = GROUND_TRUTH.get(r["claim"], "UNKNOWN")
        got = r["verdict"]
        match = "✅" if got == expected else "❌"
        print(f"{match} {r['claim'][:50]}")
        print(f"   Expected: {expected} | Got: {got}")
        if got == expected:
            correct += 1

    accuracy = round(correct / len(results) * 100, 1)
    print(f"\nAccuracy: {correct}/{len(results)} = {accuracy}%")
    return accuracy

if __name__ == "__main__":
    calculate_accuracy()
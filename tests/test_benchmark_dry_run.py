import json
import os
import shutil
import tempfile
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import benchmark


def test_benchmark_claims_schema_and_constraints():
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    claims_file = os.path.join(root, "benchmark_claims.json")
    with open(claims_file, encoding="utf-8") as f:
        claims = json.load(f)
    assert len(claims) == 50

    valid_categories = {"true", "false", "misleading", "insufficient"}
    valid_verdicts = {"TRUE", "FALSE", "MISLEADING", "INSUFFICIENT EVIDENCE"}
    for item in claims:
        assert {"id", "claim", "expected", "category"}.issubset(item.keys())
        assert item["category"] in valid_categories
        assert item["expected"] in valid_verdicts

    original_10 = {
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
    claims_map = {c["claim"]: c["expected"] for c in claims}
    for claim_text, verdict in original_10.items():
        assert claims_map.get(claim_text) == verdict

    compound_count = sum(1 for c in claims if " and " in c["claim"].lower() or " or " in c["claim"].lower())
    assert compound_count >= 5


def test_benchmark_dry_run_against_mock_http_server(monkeypatch):
    responses_by_claim = {
        "claim one": {"verdict": "TRUE", "confidence": 0.9, "papers": [{"similarity": 0.81}], "cached": False},
        "claim two": {"verdict": "TRUE", "confidence": 0.6, "papers": [{"similarity": 0.55}], "cached": False},
        "claim three": {"verdict": "MISLEADING", "confidence": 0.7, "papers": [], "cached": True},
    }

    class MockHandler(BaseHTTPRequestHandler):
        def do_POST(self):
            length = int(self.headers.get("Content-Length", "0"))
            body = json.loads(self.rfile.read(length).decode("utf-8"))
            payload = responses_by_claim.get(body["claim"])
            if payload is None:
                self.send_response(500)
                self.end_headers()
                return
            encoded = json.dumps(payload).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(encoded)))
            self.end_headers()
            self.wfile.write(encoded)

        def log_message(self, format, *args):
            return

    server = ThreadingHTTPServer(("127.0.0.1", 0), MockHandler)
    port = server.server_address[1]
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()

    work_dir = tempfile.mkdtemp(dir=os.path.dirname(os.path.abspath(__file__)))
    try:
        claims_path = os.path.join(work_dir, "claims.json")
        output_path = os.path.join(work_dir, "results.json")
        with open(claims_path, "w", encoding="utf-8") as f:
            json.dump(
                [
                    {"id": 1, "claim": "claim one", "expected": "TRUE", "category": "true"},
                    {"id": 2, "claim": "claim two", "expected": "FALSE", "category": "false"},
                    {"id": 3, "claim": "claim three", "expected": "MISLEADING", "category": "misleading"},
                ],
                f,
            )

        monkeypatch.setenv("API_URL", f"http://127.0.0.1:{port}")
        monkeypatch.setenv("BENCHMARK_CLAIMS_PATH", claims_path)
        monkeypatch.setenv("BENCHMARK_OUTPUT", output_path)
        monkeypatch.setenv("BENCHMARK_DELAY", "0")
        monkeypatch.setenv("BENCHMARK_RETRY_DELAY", "0")
        monkeypatch.setenv("BASELINE_ACCURACY", "60")

        exit_ok = benchmark.main()
        assert exit_ok == 0
        assert os.path.exists(output_path)

        with open(output_path, encoding="utf-8") as f:
            report = json.load(f)
        summary = report["summary"]
        assert summary["total"] == 3
        assert summary["correct"] == 2
        assert summary["overall_accuracy"] == 66.67
        assert summary["per_category_accuracy"]["true"]["accuracy"] == 100.0
        assert summary["per_category_accuracy"]["false"]["accuracy"] == 0.0
        assert summary["confusion_matrix"]["FALSE"]["TRUE"] == 1
        assert {"avg", "p50", "p95"} == set(summary["latency_seconds"].keys())
        assert len(report["results"]) == 3

        monkeypatch.setenv("BASELINE_ACCURACY", "80")
        exit_fail = benchmark.main()
        assert exit_fail == 1
    finally:
        server.shutdown()
        server.server_close()
        shutil.rmtree(work_dir, ignore_errors=True)

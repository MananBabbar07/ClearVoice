import ast
import importlib
import json
from pathlib import Path
from unittest.mock import MagicMock

import backend.main as main_module


def _sample_papers(pmid: str = "12345"):
    return [
        {
            "pmid": pmid,
            "title": "Sample Clinical Study",
            "journal": "BMJ",
            "year": 2024,
            "abstract": "Detailed randomized study abstract " * 5,
            "similarity": 0.82,
            "study_type": "Randomized Controlled Trial",
            "publication_types": ["Randomized Controlled Trial"],
        }
    ]


def test_load_dotenv_runs_before_retrieval_and_groq_imports():
    source = Path(main_module.__file__).read_text(encoding="utf-8")
    tree = ast.parse(source)
    load_line = None
    first_local_import = None
    local_modules = ("retrieval", "verify", "agents.judge", "agents.decomposer", "agents.explainer")
    for node in tree.body:
        if isinstance(node, ast.Expr) and isinstance(node.value, ast.Call):
            func = node.value.func
            if isinstance(func, ast.Name) and func.id == "load_dotenv":
                load_line = node.lineno
        if isinstance(node, ast.ImportFrom) and node.module in local_modules:
            if first_local_import is None:
                first_local_import = node.lineno
    assert load_line is not None
    assert first_local_import is not None
    assert load_line < first_local_import


def test_normalize_cache_key():
    assert main_module.normalize_cache_key("  Vitamin C   prevents COLDS!! ") == "v2:vitamin c prevents colds"
    assert main_module.normalize_cache_key("Smoking causes cancer?...") == "v2:smoking causes cancer"


def test_cors_allowed_origins_parsing(monkeypatch):
    monkeypatch.setenv("ALLOWED_ORIGINS", "https://app.example.com, http://localhost:5173 ")
    importlib.reload(main_module)
    assert main_module.allowed_origins == ["https://app.example.com", "http://localhost:5173"]

    monkeypatch.delenv("ALLOWED_ORIGINS", raising=False)
    importlib.reload(main_module)
    assert main_module.allowed_origins == ["*"]


def test_empty_and_whitespace_claim_returns_400(client):
    assert client.post("/verify", json={"claim": ""}).status_code == 400
    assert client.post("/verify", json={"claim": "   \n\t  "}).status_code == 400


def test_health_and_root_endpoints(client, fake_redis, monkeypatch):
    assert client.get("/").status_code == 200
    assert client.get("/health").json() == {"status": "ok", "redis": "ok"}

    monkeypatch.setattr(fake_redis, "ping", MagicMock(side_effect=RuntimeError("down")))
    assert client.get("/health").json() == {"status": "ok", "redis": "unavailable"}

    monkeypatch.setattr(main_module, "cache", None)
    assert client.get("/health").json() == {"status": "ok", "redis": "unavailable"}


def test_cache_hit_miss_and_redis_errors(client, fake_redis, monkeypatch):
    key = main_module.normalize_cache_key("exercise helps heart")
    fake_redis.set(key, json.dumps({"verdict": "TRUE", "confidence": 0.9, "cached": False}))

    hit_resp = client.post("/verify", json={"claim": "Exercise helps heart!"})
    assert hit_resp.status_code == 200
    assert hit_resp.json()["cached"] is True
    assert hit_resp.json()["verdict"] == "TRUE"

    failing_cache = MagicMock()
    failing_cache.get.side_effect = RuntimeError("redis read down")
    failing_cache.setex.side_effect = RuntimeError("redis write down")
    monkeypatch.setattr(main_module, "cache", failing_cache)
    monkeypatch.setattr(main_module, "get_similar_papers", lambda _c: _sample_papers("555"))
    monkeypatch.setattr(
        main_module,
        "get_verdict",
        lambda _c, _p: {
            "verdict": "TRUE",
            "confidence": 0.9,
            "explanation": "Supported",
            "citations": [],
            "model_used": "m1",
        },
    )
    monkeypatch.setattr(
        main_module,
        "judge_papers",
        lambda _c, _p: {
            "papers": [{"pmid": "555", "stance": "SUPPORTS"}],
            "overall_quality": "HIGH",
            "quality_explanation": "Good",
            "model_used": "m2",
        },
    )
    monkeypatch.setattr(
        main_module,
        "explain_verdict",
        lambda **_kw: {
            "plain_english": "Yes",
            "takeaway": "Keep moving",
            "evidence_strength": "Strong",
            "model_used": "m3",
        },
    )

    resp = client.post("/verify", json={"claim": "exercise helps heart"})
    assert resp.status_code == 200
    assert resp.json()["verdict"] == "TRUE"
    assert failing_cache.get.called
    assert failing_cache.setex.called


def test_determine_final_verdict_mixed_evidence():
    verdict = {"verdict": "TRUE", "confidence": 0.95, "explanation": "Initial"}
    judge_result = {"papers": [{"stance": "SUPPORTS"}, {"stance": "CONTRADICTS"}]}
    out = main_module.determine_final_verdict(verdict, judge_result)
    assert out["verdict"] == "MISLEADING"
    assert out["confidence"] == 0.7
    assert "mixed" in out["explanation"].lower()

    low_verdict = {"verdict": "TRUE", "confidence": 0.4, "explanation": ""}
    low_conf = main_module.determine_final_verdict(low_verdict, judge_result)
    assert low_conf["confidence"] == 0.4


def test_aggregate_sub_results_cases():
    single = [{"sub_claim": "c1", "verdict": "TRUE", "confidence": 0.8}]
    assert main_module.aggregate_sub_results(single) == ("TRUE", 0.8, "")

    assert main_module.aggregate_sub_results([
        {"sub_claim": "c1", "verdict": "TRUE", "confidence": 0.9},
        {"sub_claim": "c2", "verdict": "TRUE", "confidence": 0.8},
    ]) == ("TRUE", 0.8, "")

    assert main_module.aggregate_sub_results([
        {"sub_claim": "c1", "verdict": "FALSE", "confidence": 0.9},
        {"sub_claim": "c2", "verdict": "FALSE", "confidence": 0.85},
    ]) == ("FALSE", 0.85, "")

    assert main_module.aggregate_sub_results([
        {"sub_claim": "c1", "verdict": "TRUE", "confidence": 0.9},
        {"sub_claim": "c2", "verdict": "FALSE", "confidence": 0.85},
    ]) == ("MISLEADING", 0.85, "")

    assert main_module.aggregate_sub_results([
        {"sub_claim": "c1", "verdict": "INSUFFICIENT EVIDENCE", "confidence": 0.0},
        {"sub_claim": "c2", "verdict": "INSUFFICIENT EVIDENCE", "confidence": 0.0},
    ]) == ("INSUFFICIENT EVIDENCE", 0.0, "")

    verdict, conf, note = main_module.aggregate_sub_results([
        {"sub_claim": "c1", "verdict": "TRUE", "confidence": 0.8},
        {"sub_claim": "c2", "verdict": "INSUFFICIENT EVIDENCE", "confidence": 0.0},
    ])
    assert verdict == "TRUE"
    assert conf == 0.4
    assert "c2" in note

    assert main_module.aggregate_sub_results([
        {"sub_claim": "c1", "verdict": "ERROR", "confidence": 0.0},
        {"sub_claim": "c2", "verdict": "ERROR", "confidence": 0.0},
    ]) == ("ERROR", 0.0, "")


def test_verify_e2e_simple_compound_and_no_papers(client, fake_redis, monkeypatch):
    monkeypatch.setattr(
        main_module,
        "get_similar_papers",
        lambda claim: _sample_papers("101") if "smoke" in claim else _sample_papers("202"),
    )
    monkeypatch.setattr(
        main_module,
        "get_verdict",
        lambda claim, _p: {
            "verdict": "TRUE" if "smoke" in claim else "FALSE",
            "confidence": 0.9,
            "explanation": f"Exp for {claim}",
            "citations": [{"pmid": "101", "title": "Study"}],
            "model_used": "openai/gpt-oss-120b",
        },
    )
    monkeypatch.setattr(
        main_module,
        "judge_papers",
        lambda claim, papers: {
            "papers": [
                {
                    "pmid": papers[0]["pmid"],
                    "stance": "SUPPORTS",
                    "quality_score": 5,
                    "one_line_summary": "Sum",
                }
            ],
            "overall_quality": "HIGH",
            "quality_explanation": "Good",
            "model_used": "openai/gpt-oss-20b",
        },
    )
    monkeypatch.setattr(
        main_module,
        "explain_verdict",
        lambda **kw: {
            "plain_english": "Plain summary",
            "takeaway": "Takeaway",
            "evidence_strength": "Strong",
            "model_used": "openai/gpt-oss-120b",
        },
    )
    monkeypatch.setattr(
        main_module,
        "decompose_claim",
        lambda claim: {
            "is_complex": True,
            "sub_claims": ["smoke harms lungs", "bleach cures flu"],
            "original_claim": claim,
            "model_used": "openai/gpt-oss-120b",
        },
    )

    simple = client.post("/verify", json={"claim": "smoke harms lungs"})
    assert simple.status_code == 200
    simple_data = simple.json()
    assert simple_data["verdict"] == "TRUE"
    assert len(simple_data["sub_results"]) == 1
    assert simple_data["meta"]["model_used"] == {
        "decomposer": None,
        "verdict": ["openai/gpt-oss-120b"],
        "judge": ["openai/gpt-oss-20b"],
        "explainer": "openai/gpt-oss-120b",
    }
    assert fake_redis.get(main_module.normalize_cache_key("smoke harms lungs")) is not None

    compound = client.post("/verify", json={"claim": "smoke harms lungs and bleach cures flu"})
    assert compound.status_code == 200
    comp_data = compound.json()
    assert comp_data["verdict"] == "MISLEADING"
    assert len(comp_data["sub_results"]) == 2
    assert comp_data["meta"]["model_used"]["decomposer"] == "openai/gpt-oss-120b"
    assert len(comp_data["meta"]["model_used"]["verdict"]) == 2

    monkeypatch.setattr(main_module, "get_similar_papers", lambda _c: [])
    no_papers = client.post("/verify", json={"claim": "obscure unsupported claim"})
    assert no_papers.status_code == 200
    np_data = no_papers.json()
    assert np_data["verdict"] == "INSUFFICIENT EVIDENCE"
    assert np_data["confidence"] == 0.0
    assert fake_redis.get(main_module.normalize_cache_key("obscure unsupported claim")) is None


def test_no_caching_when_partial_no_papers_or_error(client, fake_redis, monkeypatch):
    monkeypatch.setattr(
        main_module,
        "decompose_claim",
        lambda claim: {
            "is_complex": True,
            "sub_claims": ["claim a", "claim b"],
            "original_claim": claim,
            "model_used": "m-dec",
        },
    )
    monkeypatch.setattr(main_module, "get_similar_papers", lambda c: _sample_papers("1") if c == "claim a" else [])
    monkeypatch.setattr(
        main_module,
        "get_verdict",
        lambda _c, _p: {
            "verdict": "TRUE",
            "confidence": 0.9,
            "explanation": "Yes",
            "citations": [],
            "model_used": "m-ver",
        },
    )
    monkeypatch.setattr(
        main_module,
        "judge_papers",
        lambda _c, _p: {
            "papers": [{"pmid": "1", "stance": "SUPPORTS"}],
            "overall_quality": "HIGH",
            "quality_explanation": "Ok",
            "model_used": "m-jdg",
        },
    )
    monkeypatch.setattr(
        main_module,
        "explain_verdict",
        lambda **_kw: {
            "plain_english": "Plain",
            "takeaway": "Tip",
            "evidence_strength": "Moderate",
            "model_used": "m-exp",
        },
    )

    partial = client.post("/verify", json={"claim": "claim a and claim b"})
    assert partial.status_code == 200
    assert partial.json()["verdict"] == "TRUE"
    assert partial.json()["confidence"] == 0.45
    assert fake_redis.get(main_module.normalize_cache_key("claim a and claim b")) is None

    monkeypatch.setattr(main_module, "get_similar_papers", lambda _c: _sample_papers("1"))
    monkeypatch.setattr(
        main_module,
        "get_verdict",
        lambda c, _p: {
            "verdict": "ERROR" if c == "claim b" else "TRUE",
            "confidence": 0.0,
            "explanation": "Err",
            "citations": [],
            "model_used": "m-ver",
        },
    )
    err_resp = client.post("/verify", json={"claim": "claim a and claim b"})
    assert err_resp.status_code == 200
    assert fake_redis.get(main_module.normalize_cache_key("claim a and claim b")) is None

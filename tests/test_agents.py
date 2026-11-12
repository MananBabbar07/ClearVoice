import json

import verify
from agents import decomposer, explainer, judge


def test_judge_papers_positional_injection_and_validation(mock_call_groq):
    papers = [
        {
            "pmid": "111",
            "title": "Paper A",
            "journal": "J1",
            "year": 2022,
            "abstract": "Text A",
            "study_type": "Meta-Analysis",
        },
        {
            "pmid": "222",
            "title": "Paper B",
            "journal": "J2",
            "year": 2021,
            "abstract": "Text B",
            "study_type": "Review",
        },
    ]
    payload = {
        "papers": [
            {"paper_number": 9, "stance": "SUPPORTS", "quality_score": 5, "one_line_summary": "Supports"},
            {"paper_number": 7, "stance": "contradicts", "quality_score": 4, "one_line_summary": "Contradicts"},
        ],
        "overall_quality": "HIGH",
        "quality_explanation": "Solid evidence.",
    }
    mock_call_groq.return_value = (json.dumps(payload), "openai/gpt-oss-20b")

    result = judge.judge_papers("exercise helps health", papers)
    assert result["model_used"] == "openai/gpt-oss-20b"
    assert len(result["papers"]) == 2
    assert result["papers"][0]["paper_number"] == 1
    assert result["papers"][0]["pmid"] == "111"
    assert result["papers"][0]["study_type"] == "Meta-Analysis"
    assert result["papers"][1]["paper_number"] == 2
    assert result["papers"][1]["pmid"] == "222"
    assert result["papers"][1]["study_type"] == "Review"
    assert result["papers"][1]["stance"] == "CONTRADICTS"

    validator = mock_call_groq.call_args.kwargs["validator"]
    assert validator(json.dumps(payload)) is True
    assert validator(json.dumps({"papers": [payload["papers"][0]]})) is False
    assert validator(json.dumps({"papers": [{"stance": "INVALID"}, {"stance": "SUPPORTS"}]})) is False
    assert validator("not json") is False


def test_judge_papers_malformed_json_fallback(mock_call_groq):
    papers = [{"pmid": "111", "title": "P", "journal": "J", "year": 2020, "abstract": "Abs", "study_type": "Other"}]
    mock_call_groq.return_value = ("not valid json at all", "openai/gpt-oss-120b")

    result = judge.judge_papers("claim", papers)
    assert result["papers"] == []
    assert result["overall_quality"] == "UNKNOWN"
    assert result["model_used"] == "openai/gpt-oss-120b"


def test_verify_and_agents_extract_json_and_fallbacks(mock_call_groq):
    verdict_json = '{"verdict": "TRUE", "confidence": 0.9, "explanation": "Yes", "citations": []}'
    mock_call_groq.return_value = (f"prefix {verdict_json} suffix", "m1")
    sample = [{"pmid": "1", "title": "T", "journal": "J", "year": 2023, "abstract": "A", "similarity": 0.8}]
    res = verify.get_verdict("claim", sample)
    assert res["verdict"] == "TRUE"
    assert res["model_used"] == "m1"

    mock_call_groq.return_value = (None, None)
    err = verify.get_verdict("claim", [])
    assert err["verdict"] == "ERROR"

    mock_call_groq.return_value = (
        '{"is_complex": true, "sub_claims": ["a", "b"], "original_claim": "a and b"}',
        "m-dec",
    )
    dec_ok = decomposer.decompose_claim("a and b")
    assert dec_ok["is_complex"] is True
    assert dec_ok["model_used"] == "m-dec"

    mock_call_groq.return_value = ("not json", None)
    dec_fallback = decomposer.decompose_claim("simple claim")
    assert dec_fallback["sub_claims"] == ["simple claim"]

    mock_call_groq.return_value = (
        'wrap {"plain_english": "Clear.", "takeaway": "Tip.", "evidence_strength": "Strong"} end',
        "m-exp",
    )
    exp_ok = explainer.explain_verdict("claim", "TRUE", 0.9, "Tech exp", {})
    assert exp_ok["plain_english"] == "Clear."
    assert exp_ok["model_used"] == "m-exp"

    mock_call_groq.return_value = ("bad", None)
    exp_fallback = explainer.explain_verdict("claim", "TRUE", 0.9, "Tech exp", {})
    assert exp_fallback["plain_english"] == "Tech exp"

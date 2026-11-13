from unittest.mock import MagicMock

import numpy as np
import retrieval


def _pubmed_article(pmid: str, abstract: str, pub_types: list, year: str = "2023"):
    return {
        "MedlineCitation": {
            "PMID": pmid,
            "Article": {
                "ArticleTitle": f"Title {pmid}",
                "Abstract": {"AbstractText": [abstract]},
                "Journal": {"Title": "Medical Journal", "JournalIssue": {"PubDate": {"Year": year}}},
                "AuthorList": [{"LastName": "Doe", "ForeName": "Jane"}],
                "PublicationTypeList": pub_types,
            },
        }
    }


def test_map_study_type_all_mappings():
    assert retrieval.map_study_type([]) == "Other"
    assert retrieval.map_study_type(["Meta-Analysis"]) == "Meta-Analysis"
    assert retrieval.map_study_type(["Systematic Review"]) == "Systematic Review"
    assert retrieval.map_study_type(["Randomized Controlled Trial"]) == "Randomized Controlled Trial"
    assert retrieval.map_study_type(["Clinical Trial"]) == "Clinical Trial"
    assert retrieval.map_study_type(["Clinical Trial, Phase III"]) == "Clinical Trial"
    assert retrieval.map_study_type(["Review"]) == "Review"
    assert retrieval.map_study_type(["Case Reports"]) == "Case Reports"
    assert retrieval.map_study_type(["Case Report"]) == "Case Reports"
    assert retrieval.map_study_type(["Observational Study"]) == "Observational Study"
    assert retrieval.map_study_type(["Prospective Observational Study"]) == "Observational Study"
    assert retrieval.map_study_type(["Journal Article"]) == "Other"


def test_cosine_similarity_edge_cases():
    assert retrieval.cosine_similarity([0.0, 0.0], [1.0, 0.0]) == 0.0
    assert abs(retrieval.cosine_similarity([1.0, 0.0], [1.0, 0.0]) - 1.0) < 1e-6


def test_sim_threshold_filtering(monkeypatch, mock_entrez, mock_sentence_transformer):
    monkeypatch.setenv("SIM_THRESHOLD", "0.50")

    search_handle = MagicMock()
    fetch_handle = MagicMock()
    mock_entrez.esearch.return_value = search_handle
    mock_entrez.efetch.return_value = fetch_handle

    long_abs = "A" * 150
    mock_entrez.read.side_effect = [
        {"IdList": ["100", "200"]},
        {
            "PubmedArticle": [
                _pubmed_article("100", long_abs, ["Meta-Analysis"]),
                _pubmed_article("200", long_abs, ["Review"]),
            ]
        },
    ]

    def encode_side_effect(text_or_list, **kwargs):
        if isinstance(text_or_list, list):
            return np.array([[1.0, 0.0], [0.2, 0.98]])
        return np.array([1.0, 0.0])

    mock_sentence_transformer.encode.side_effect = encode_side_effect

    papers = retrieval.get_similar_papers("test claim", top_k=5)
    assert len(papers) == 1
    assert papers[0]["pmid"] == "100"
    assert papers[0]["similarity"] == 1.0
    assert papers[0]["study_type"] == "Meta-Analysis"


def test_sim_threshold_invalid_falls_back_to_default(monkeypatch, mock_entrez, mock_sentence_transformer):
    monkeypatch.setenv("SIM_THRESHOLD", "not-a-float")
    mock_entrez.esearch.return_value = MagicMock()
    mock_entrez.read.return_value = {"IdList": []}

    assert retrieval.get_similar_papers("empty claim") == []


def test_entrez_call_retries_and_errors(mock_entrez):
    handle = MagicMock()
    mock_entrez.esearch.return_value = handle
    mock_entrez.read.side_effect = [RuntimeError("transient"), {"IdList": ["1"]}]

    assert retrieval.search_pubmed_live("claim") == ["1"]
    assert handle.close.called

    mock_entrez.read.side_effect = RuntimeError("permanent")
    assert retrieval.search_pubmed_live("claim") == []


def test_fetch_abstracts_live_empty_and_error(mock_entrez):
    assert retrieval.fetch_abstracts_live([]) == []
    mock_entrez.efetch.side_effect = RuntimeError("fetch failure")
    assert retrieval.fetch_abstracts_live(["123"]) == []

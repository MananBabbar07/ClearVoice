import logging
import os
import threading
import time

import numpy as np
from Bio import Entrez
from dotenv import load_dotenv
from sentence_transformers import SentenceTransformer

load_dotenv()

logger = logging.getLogger(__name__)

Entrez.email = os.getenv("NCBI_EMAIL", "your@email.com")
ncbi_api_key = os.getenv("NCBI_API_KEY")
if ncbi_api_key:
    Entrez.api_key = ncbi_api_key

model = SentenceTransformer("NeuML/pubmedbert-base-embeddings")

_entrez_lock = threading.Lock()
_embed_lock = threading.Lock()
_last_entrez_call = 0.0
_entrez_min_interval = 0.11 if ncbi_api_key else 0.35

TARGET_STUDY_TYPES = [
    "Meta-Analysis",
    "Systematic Review",
    "Randomized Controlled Trial",
    "Clinical Trial",
    "Review",
    "Case Reports",
    "Observational Study",
]


def map_study_type(publication_types: list) -> str:
    if not publication_types:
        return "Other"
    lowered = [pt.strip().lower() for pt in publication_types if pt]
    for target in TARGET_STUDY_TYPES:
        if target.lower() in lowered:
            return target
    for pt_low in lowered:
        if "clinical trial" in pt_low:
            return "Clinical Trial"
        if "observational study" in pt_low:
            return "Observational Study"
        if "case report" in pt_low:
            return "Case Reports"
    return "Other"


def _entrez_call(func, *args, retries: int = 2, **kwargs):
    global _last_entrez_call
    for attempt in range(retries + 1):
        with _entrez_lock:
            elapsed = time.monotonic() - _last_entrez_call
            if elapsed < _entrez_min_interval:
                time.sleep(_entrez_min_interval - elapsed)
            _last_entrez_call = time.monotonic()
        try:
            handle = func(*args, **kwargs)
            record = Entrez.read(handle)
            handle.close()
            return record
        except Exception as e:
            if attempt < retries:
                logger.warning("Entrez call failed (attempt %d/%d): %s", attempt + 1, retries + 1, e)
                time.sleep(0.5 * (attempt + 1))
            else:
                raise


def cosine_similarity(a, b):
    a = np.array(a)
    b = np.array(b)
    denom = np.linalg.norm(a) * np.linalg.norm(b)
    if denom == 0:
        return 0.0
    return float(np.dot(a, b) / denom)


def search_pubmed_live(query: str, max_results: int = 20) -> list:
    try:
        record = _entrez_call(Entrez.esearch, db="pubmed", term=query, retmax=max_results, sort="relevance")
        return record["IdList"]
    except Exception as e:
        logger.warning("PubMed search error: %s", e)
        return []


def fetch_abstracts_live(pmids: list) -> list:
    if not pmids:
        return []
    try:
        ids = ",".join(pmids)
        records = _entrez_call(Entrez.efetch, db="pubmed", id=ids, rettype="xml", retmode="xml")

        papers = []
        for article in records["PubmedArticle"]:
            try:
                medline = article["MedlineCitation"]
                art = medline["Article"]

                pmid = str(medline["PMID"])
                title = str(art.get("ArticleTitle", ""))
                abstract_text = art.get("Abstract", {}).get("AbstractText", [""])
                abstract = " ".join([str(a) for a in abstract_text])
                journal = str(art["Journal"]["Title"])
                year = int(art["Journal"]["JournalIssue"]["PubDate"].get("Year", 0) or 0)
                authors = []
                for a in art.get("AuthorList", []):
                    name = f"{a.get('LastName', '')} {a.get('ForeName', '')}".strip()
                    if name:
                        authors.append(name)
                publication_types = [str(pt) for pt in art.get("PublicationTypeList", [])]

                if abstract and len(abstract) > 100:
                    papers.append({
                        "pmid": pmid,
                        "title": title,
                        "abstract": abstract,
                        "journal": journal,
                        "year": year,
                        "authors": authors,
                        "publication_types": publication_types,
                        "study_type": map_study_type(publication_types),
                    })
            except Exception:
                continue

        return papers
    except Exception as e:
        logger.warning("PubMed fetch error: %s", e)
        return []


def get_similar_papers(claim: str, top_k: int = 5) -> list:
    try:
        sim_threshold = float(os.getenv("SIM_THRESHOLD", "0.30"))
    except ValueError:
        sim_threshold = 0.30

    with _embed_lock:
        claim_embedding = model.encode(claim).tolist()

    pmids = search_pubmed_live(claim, max_results=20)

    if not pmids:
        return []

    papers = fetch_abstracts_live(pmids)

    if not papers:
        return []

    abstracts = [p["abstract"] for p in papers]
    with _embed_lock:
        embeddings = model.encode(abstracts, batch_size=16).tolist()

    scored = []
    for paper, embedding in zip(papers, embeddings):
        similarity = cosine_similarity(claim_embedding, embedding)
        paper["similarity"] = round(float(similarity), 2)
        scored.append(paper)

    scored.sort(key=lambda x: x["similarity"], reverse=True)
    filtered = [p for p in scored if p["similarity"] >= sim_threshold]
    top_sim = scored[0]["similarity"] if scored else 0.0
    logger.info(
        "[Retrieval] claim=%r top_similarity=%.2f kept=%d/%d threshold=%.2f",
        claim,
        top_sim,
        len(filtered),
        len(scored),
        sim_threshold,
    )
    return filtered[:top_k]


if __name__ == "__main__":
    claim = input("Enter a health claim: ")
    papers = get_similar_papers(claim)
    for p in papers:
        print(f"\n[{p['similarity']:.2f}] {p['title']} ({p['year']})")
        print(f"  Journal: {p['journal']}")
        print(f"  PMID: {p['pmid']}")

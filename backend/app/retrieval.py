import os
import time
from dotenv import load_dotenv
from Bio import Entrez
from sentence_transformers import SentenceTransformer
import numpy as np

load_dotenv()

Entrez.email = os.getenv("NCBI_EMAIL", "your@email.com")

model = SentenceTransformer("NeuML/pubmedbert-base-embeddings")


def cosine_similarity(a, b):
    a = np.array(a)
    b = np.array(b)
    return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))


def search_pubmed_live(query: str, max_results: int = 20) -> list:
    try:
        handle = Entrez.esearch(db="pubmed", term=query, retmax=max_results, sort="relevance")
        record = Entrez.read(handle)
        handle.close()
        return record["IdList"]
    except Exception as e:
        print(f"PubMed search error: {e}")
        return []


def fetch_abstracts_live(pmids: list) -> list:
    if not pmids:
        return []
    try:
        ids = ",".join(pmids)
        handle = Entrez.efetch(db="pubmed", id=ids, rettype="xml", retmode="xml")
        records = Entrez.read(handle)
        handle.close()

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

                if abstract and len(abstract) > 100:
                    papers.append({
                        "pmid": pmid,
                        "title": title,
                        "abstract": abstract,
                        "journal": journal,
                        "year": year,
                        "authors": authors,
                    })
            except Exception:
                continue

        return papers
    except Exception as e:
        print(f"PubMed fetch error: {e}")
        return []


def get_similar_papers(claim: str, top_k: int = 5) -> list:
    # Embed the claim
    claim_embedding = model.encode(claim).tolist()

    # Search PubMed live
    pmids = search_pubmed_live(claim, max_results=20)

    if not pmids:
        return []

  
    papers = fetch_abstracts_live(pmids)

    if not papers:
        return []

    
    abstracts = [p["abstract"] for p in papers]
    embeddings = model.encode(abstracts, batch_size=16).tolist()

    scored = []
    for paper, embedding in zip(papers, embeddings):
        similarity = cosine_similarity(claim_embedding, embedding)
        paper["similarity"] = round(float(similarity), 2)
        scored.append(paper)

    #
    scored.sort(key=lambda x: x["similarity"], reverse=True)
    return scored[:top_k]


if __name__ == "__main__":
    claim = input("Enter a health claim: ")
    papers = get_similar_papers(claim)
    for p in papers:
        print(f"\n[{p['similarity']:.2f}] {p['title']} ({p['year']})")
        print(f"  Journal: {p['journal']}")
        print(f"  PMID: {p['pmid']}")
import os
import time
import psycopg2
from dotenv import load_dotenv
from Bio import Entrez
from sentence_transformers import SentenceTransformer
from database import get_connection

load_dotenv()

Entrez.email = os.getenv("NCBI_EMAIL", "your@email.com")

model = SentenceTransformer("all-MiniLM-L6-v2")

SEARCH_TERMS = [
    "cancer treatment",
    "diabetes management",
    "vaccine safety",
    "vitamin supplements",
    "covid treatment",
    "blood pressure",
    "heart disease prevention",
    "antibiotic resistance",
]


def fetch_pubmed_ids(term: str, max_results: int = 500) -> list:
    handle = Entrez.esearch(db="pubmed", term=term, retmax=max_results)
    record = Entrez.read(handle)
    handle.close()
    return record["IdList"]


def fetch_abstracts(pmids: list) -> list:
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
        except Exception as e:
            continue

    return papers


def store_papers(papers: list):
    conn = get_connection()
    cur = conn.cursor()
    stored = 0

    for paper in papers:
        try:
            embedding = model.encode(paper["abstract"]).tolist()

            cur.execute("""
                INSERT INTO studies (pmid, title, abstract, authors, year, journal, embedding)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (pmid) DO NOTHING
            """, (
                paper["pmid"],
                paper["title"],
                paper["abstract"],
                paper["authors"],
                paper["year"],
                paper["journal"],
                embedding,
            ))
            stored += 1

        except Exception as e:
            print(f"Error storing {paper['pmid']}: {e}")
            conn.rollback()
            continue

    conn.commit()
    cur.close()
    conn.close()
    print(f"Stored {stored} papers.")


def run_ingestion(max_per_term: int = 500):
    total = 0
    for term in SEARCH_TERMS:
        print(f"Fetching: {term}")
        pmids = fetch_pubmed_ids(term, max_per_term)
        print(f"  Found {len(pmids)} papers")
        papers = fetch_abstracts(pmids)
        print(f"  Fetched {len(papers)} abstracts")
        store_papers(papers)
        total += len(papers)
        time.sleep(1)  # be polite to NCBI API

    print(f"\nIngestion complete. Total papers processed: {total}")


if __name__ == "__main__":
    run_ingestion()
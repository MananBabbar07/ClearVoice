import os
import time
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
    "smoking lung cancer",
    "vitamin C common cold",
    "sugar insulin resistance",
    "stress hypertension",
    "autism spectrum disorder",
    "vaccine adverse effects",
    "mental health depression",
    "sleep deprivation effects",
    "intermittent fasting",
    "obesity metabolic syndrome",
    "alcohol liver disease",
    "exercise mental health",
    "gut microbiome health",
    "meditation stress reduction",
    "processed food inflammation",
    "statin heart disease",
    "homeopathy clinical evidence",
    "essential oils therapeutic effects",
    "acupuncture pain management",
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

    abstracts = [paper["abstract"] for paper in papers]
    embeddings = model.encode(abstracts, batch_size=64, show_progress_bar=True).tolist()

    for paper, embedding in zip(papers, embeddings):
        try:
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
        time.sleep(1)

    print(f"\nIngestion complete. Total papers processed: {total}")


if __name__ == "__main__":
    run_ingestion()
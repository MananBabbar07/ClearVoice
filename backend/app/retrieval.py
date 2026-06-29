import os
from dotenv import load_dotenv
from sentence_transformers import SentenceTransformer
from database import get_connection

load_dotenv()
model = SentenceTransformer("NeuML/pubmedbert-base-embeddings")


def get_similar_papers(claim: str, top_k: int = 5) -> list:
    embedding = model.encode(claim).tolist()

    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT pmid, title, abstract, authors, year, journal,
               1 - (biobert_embedding <=> %s::vector) AS similarity
        FROM studies
        WHERE biobert_embedding IS NOT NULL
        ORDER BY biobert_embedding <=> %s::vector
        LIMIT %s
    """, (embedding, embedding, top_k))

    results = cur.fetchall()
    cur.close()
    conn.close()

    return [dict(row) for row in results]


if __name__ == "__main__":
    claim = input("Enter a health claim: ")
    papers = get_similar_papers(claim)
    for p in papers:
        print(f"\n[{p['similarity']:.2f}] {p['title']} ({p['year']})")
        print(f"  Journal: {p['journal']}")
        print(f"  PMID: {p['pmid']}")
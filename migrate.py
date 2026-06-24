import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv
import os

load_dotenv(dotenv_path='E:/ClearVoice/.env', override=True)


local_conn = psycopg2.connect(os.getenv('DATABASE_URL'), cursor_factory=RealDictCursor)
local_cur = local_conn.cursor()

supa_conn = psycopg2.connect(os.getenv('SUPABASE_DATABASE_URL'))
supa_cur = supa_conn.cursor()

print("Fetching papers from local DB...")
local_cur.execute("SELECT pmid, title, abstract, authors, year, journal, study_type, embedding FROM studies")
papers = local_cur.fetchall()
print(f"Found {len(papers)} papers. Migrating...")

for i, paper in enumerate(papers):
    try:
        supa_cur.execute("""
            INSERT INTO studies (pmid, title, abstract, authors, year, journal, study_type, embedding)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (pmid) DO NOTHING
        """, (
            paper['pmid'],
            paper['title'],
            paper['abstract'],
            paper['authors'],
            paper['year'],
            paper['journal'],
            paper['study_type'],
            paper['embedding']
        ))

        if (i + 1) % 100 == 0:
            supa_conn.commit()
            print(f"  Migrated {i + 1} papers...")

    except Exception as e:
        print(f"Error on {paper['pmid']}: {e}")
        supa_conn.rollback()
        continue

supa_conn.commit()
local_cur.close()
local_conn.close()
supa_cur.close()
supa_conn.close()
print(f"Migration complete. {len(papers)} papers migrated to Supabase.")
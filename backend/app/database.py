import psycopg2
from psycopg2.extras import RealDictCursor
import os
from dotenv import load_dotenv

load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")


def get_connection():
    return psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor)


def setup_database():
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("CREATE EXTENSION IF NOT EXISTS vector;")

  
    cur.execute("""
        CREATE TABLE IF NOT EXISTS studies (
            id          SERIAL PRIMARY KEY,
            pmid        TEXT UNIQUE NOT NULL,
            title       TEXT,
            abstract    TEXT,
            authors     TEXT[],
            year        INT,
            journal     TEXT,
            study_type  TEXT,
            embedding   vector(384)
        );
    """)


    cur.execute("""
        CREATE INDEX IF NOT EXISTS studies_embedding_idx
        ON studies
        USING ivfflat (embedding vector_cosine_ops)
        WITH (lists = 100);
    """)

    conn.commit()
    cur.close()
    conn.close()
    print("Database setup complete.")


if __name__ == "__main__":
    setup_database()
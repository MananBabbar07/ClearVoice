from dotenv import load_dotenv
import os
import psycopg2

load_dotenv(dotenv_path='E:/ClearVoice/.env', override=True)

conn = psycopg2.connect(os.getenv('SUPABASE_DATABASE_URL'))
cur = conn.cursor()

cur.execute('CREATE EXTENSION IF NOT EXISTS vector;')

cur.execute('''
    CREATE TABLE IF NOT EXISTS studies (
        id SERIAL PRIMARY KEY,
        pmid TEXT UNIQUE NOT NULL,
        title TEXT,
        abstract TEXT,
        authors TEXT[],
        year INT,
        journal TEXT,
        study_type TEXT,
        embedding vector(384)
    );
''')

cur.execute('''
    CREATE INDEX IF NOT EXISTS studies_embedding_idx
    ON studies
    USING ivfflat (embedding vector_cosine_ops)
    WITH (lists = 100);
''')

conn.commit()
cur.close()
conn.close()
print('Supabase schema created.')
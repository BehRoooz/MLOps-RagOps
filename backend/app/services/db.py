"""
This module is used to interact with the database.

It uses the psycopg2 library to connect to the database.
It uses the contextlib library to manage the database connection.
It uses the app.core.config module to get the database connection string.
It uses the app.core.logging module to log messages.
"""

import psycopg2
import psycopg2.extras
from contextlib import contextmanager
from app.core.config import settings
from app.core.logging import logger

# Get a database connection
@contextmanager
def get_db_connection():
    conn = psycopg2.connect(settings.POSTGRES_URL)
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()

# Insert document metadata into the database
def insert_document_metadata(filename: str, minio_path: str, 
                             chunk_count: int, embedding_model: str) -> int:

    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """ INSERT INTO documents (filename, minio_path, chunk_count, embedding_model) 
                    VALUES (%s, %s, %s, %s) RETURNING document_id """,
                    (filename, minio_path, chunk_count, embedding_model),
            )
            return cur.fetchone()[0]

# Get document metadata from the database
def get_document_metadata(document_id: int) -> dict | None:
    with get_db_connection() as conn:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute("SELECT * FROM documents WHERE document_id = %s", (document_id,))
            row = cur.fetchone()
            return dict(row) if row else None

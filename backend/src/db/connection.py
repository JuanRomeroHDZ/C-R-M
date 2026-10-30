import contextlib
import psycopg
from psycopg.rows import dict_row
from src.config import settings


@contextlib.contextmanager
def get_db_connection():
    conn = psycopg.connect(settings.postgres_conninfo, row_factory=dict_row)
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def execute_query(query: str, params: tuple = ()):
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(query, params)
            if cur.description:
                return cur.fetchall()
            return []


def execute_mutation(query: str, params: tuple = ()):
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(query, params)
            return cur.rowcount

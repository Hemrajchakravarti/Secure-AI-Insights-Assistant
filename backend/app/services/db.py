# -*- coding: utf-8 -*-
"""app/services/db.py"""
import os, sqlite3, logging
from contextlib import contextmanager

logger  = logging.getLogger(__name__)
DB_PATH = os.environ.get(
    "DB_PATH",
    os.path.join(os.path.dirname(__file__), "../../data/db/insights.db"),
)

def init_db():
    if not os.path.exists(DB_PATH):
        raise RuntimeError(
            f"Database not found at {DB_PATH}.\n"
            "Run:  python setup.py  (from the project root)"
        )
    logger.info("Database OK: %s", DB_PATH)

@contextmanager
def get_db():
    conn = sqlite3.connect(f"file:{DB_PATH}?mode=ro", uri=True)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()

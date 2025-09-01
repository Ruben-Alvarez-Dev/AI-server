#!/usr/bin/env python3
"""
LanceDB Configuration (stub with graceful fallback)

Provides helpers for LanceDB setup when the package is available.
"""

from pathlib import Path
from typing import Optional


LANCEDB_DIR = Path("services/storage/data/lancedb")


def ensure_lancedb_dir() -> None:
    LANCEDB_DIR.mkdir(parents=True, exist_ok=True)


def get_db(path: Optional[str] = None):
    """Return a LanceDB connection if lancedb is installed, else raise informative error."""
    try:
        import lancedb
    except Exception as e:
        raise RuntimeError("LanceDB is not installed. Please `pip install lancedb`. ") from e

    ensure_lancedb_dir()
    db_path = Path(path) if path else LANCEDB_DIR
    return lancedb.connect(str(db_path))


if __name__ == "__main__":
    try:
        db = get_db()
        print("LanceDB connected:", db)
    except Exception as e:
        print("LanceDB unavailable:", e)


#!/usr/bin/env python3
"""
SQLite Configuration and Initialization

Verifies SQLite version, applies PRAGMAs (WAL, cache size, etc.), and provides
helpers to create and connect to SQLite databases used by the system.
"""

import os
import sqlite3
from pathlib import Path
from typing import Tuple


SQLITE_DIR = Path("services/storage/data/sqlite")


def ensure_sqlite_dir() -> None:
    SQLITE_DIR.mkdir(parents=True, exist_ok=True)


def parse_version(version: str) -> Tuple[int, int, int]:
    parts = (version.split(".") + ["0", "0"])[:3]
    return tuple(int(p) for p in parts)


def verify_sqlite(min_version: str = "3.35.0") -> bool:
    """Verify SQLite runtime version meets minimum requirements."""
    runtime = sqlite3.sqlite_version
    ok = parse_version(runtime) >= parse_version(min_version)
    return ok


def configure_connection(conn: sqlite3.Connection, cache_mb: int = 500) -> None:
    """Apply recommended PRAGMA settings to a connection."""
    cur = conn.cursor()
    # WAL journaling and normal sync for performance
    cur.execute("PRAGMA journal_mode=WAL;")
    cur.execute("PRAGMA synchronous=NORMAL;")
    # Cache size in KB with negative value
    cur.execute(f"PRAGMA cache_size=-{cache_mb * 1000};")
    # Keep temp data in memory
    cur.execute("PRAGMA temp_store=MEMORY;")
    # Enable incremental vacuum and foreign keys
    cur.execute("PRAGMA foreign_keys=ON;")
    cur.execute("PRAGMA auto_vacuum=FULL;")
    cur.close()


def connect(db_name: str) -> sqlite3.Connection:
    """Connect to a named DB under the SQLite data directory and configure it."""
    ensure_sqlite_dir()
    db_path = SQLITE_DIR / f"{db_name}.db"
    conn = sqlite3.connect(str(db_path))
    configure_connection(conn)
    return conn


if __name__ == "__main__":
    ensure_sqlite_dir()
    print(f"SQLite runtime: {sqlite3.sqlite_version}")
    print(f"Meets 3.35.0+: {verify_sqlite()}")
    with connect("test") as c:
        c.execute("CREATE TABLE IF NOT EXISTS ping(id INTEGER PRIMARY KEY, t TEXT);")
        c.execute("INSERT INTO ping(t) VALUES('ok');")
        print("Ping:", c.execute("SELECT COUNT(*) FROM ping").fetchone()[0])


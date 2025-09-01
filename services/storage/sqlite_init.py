#!/usr/bin/env python3
"""
SQLite Databases Initialization

Creates and initializes SQLite databases for configuration, axioms, and
permanent storage with recommended PRAGMAs.
"""

from pathlib import Path
from typing import Dict
from sqlite_config import connect, ensure_sqlite_dir


SCHEMAS: Dict[str, str] = {
    "config": """
        CREATE TABLE IF NOT EXISTS system_config (
            key TEXT PRIMARY KEY,
            value TEXT NOT NULL,
            type TEXT DEFAULT 'string',
            description TEXT,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
        );
    """,
    "axioms": """
        CREATE TABLE IF NOT EXISTS axioms (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE,
            definition TEXT NOT NULL,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        );
    """,
    "permanent": """
        CREATE TABLE IF NOT EXISTS permanent_store (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            kind TEXT NOT NULL,
            content TEXT NOT NULL,
            tags TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        );
    """,
}


def initialize_all() -> None:
    ensure_sqlite_dir()
    for db in ("config", "axioms", "permanent"):
        with connect(db) as conn:
            conn.executescript(SCHEMAS[db])
            # Vacuum to apply auto_vacuum=FULL
            conn.execute("VACUUM;")


if __name__ == "__main__":
    initialize_all()
    print("Initialized SQLite databases: config, axioms, permanent")


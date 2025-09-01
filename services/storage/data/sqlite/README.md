# SQLite Data Directory

Stores SQLite databases used for lightweight configuration and persistent key-value storage.

Databases
- config.db: system_config key/value
- axioms.db: axioms definitions
- permanent.db: generic permanent storage

PRAGMAs
- WAL journaling, synchronous=NORMAL
- cache_size ~ 500MB (negative KB)
- auto_vacuum=FULL, temp_store=MEMORY, foreign_keys=ON


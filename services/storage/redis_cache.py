#!/usr/bin/env python3
"""
Redis-compatible cache client for DragonflyDB.

Provides minimal helpers to validate compatibility: PING, GET/SET/EXPIRE.
"""

from typing import Optional


def get_client(host: str = "127.0.0.1", port: int = 6379, db: int = 0):
    try:
        import redis
    except Exception as e:
        raise RuntimeError("Redis python client is required. Install `pip install redis`. ") from e

    return redis.Redis(host=host, port=port, db=db, decode_responses=True)


def self_test(host: str = "127.0.0.1", port: int = 6379) -> bool:
    r = get_client(host, port)
    assert r.ping() is True
    assert r.set("cache:test", "ok", ex=10) is True
    assert r.get("cache:test") == "ok"
    return True


if __name__ == "__main__":
    try:
        ok = self_test()
        print("Dragonfly/Redis compatibility OK:", ok)
    except Exception as e:
        print("Cache self-test failed:", e)


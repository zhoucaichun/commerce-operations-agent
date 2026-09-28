"""Initialize the local SQLite schema and synthetic Commerce seed data."""

from __future__ import annotations

import argparse

from commerce_agent.sqlite_store import SQLiteStore


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Initialize synthetic Commerce Agent storage")
    parser.add_argument("--database", default="commerce-agent.sqlite3")
    arguments = parser.parse_args()
    store = SQLiteStore(arguments.database)
    store.ready()
    print(f"initialized synthetic Commerce Agent storage: {arguments.database}")
    store.close()

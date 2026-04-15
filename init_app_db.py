from __future__ import annotations

import sqlite3
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "app.db"
SCHEMA_PATH = BASE_DIR / "schema.sql"


def init_db() -> None:
    if not SCHEMA_PATH.exists():
        raise FileNotFoundError(f"No existe el archivo de esquema: {SCHEMA_PATH}")

    with sqlite3.connect(DB_PATH) as conn:
        conn.executescript(SCHEMA_PATH.read_text(encoding="utf-8"))
        conn.commit()


if __name__ == "__main__":
    init_db()
    print(f"Base de datos generada en: {DB_PATH}")

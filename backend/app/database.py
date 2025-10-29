from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Iterable

from .config import get_settings
from .models import MunicipalityCache, ObjectRecord

settings = get_settings()


def _resolve_path(url: str) -> Path:
    if not url.startswith("sqlite:///"):
        raise ValueError("Pouze SQLite je podporováno")
    path = url.replace("sqlite:///", "", 1)
    return Path(path).resolve()


def _ensure_schema(conn: sqlite3.Connection) -> None:
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS municipality_cache (
            kod_obce TEXT PRIMARY KEY,
            name TEXT,
            created_at TEXT,
            raw_source TEXT
        )
        """
    )
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS objects (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            kod_obce TEXT,
            kod_stavebni_objekt TEXT,
            typ TEXT,
            byty_odhad INTEGER,
            letaky INTEGER,
            lon REAL,
            lat REAL,
            ulice TEXT,
            cp_ce TEXT,
            cast_obce TEXT,
            psc TEXT,
            nejiste INTEGER
        )
        """
    )
    conn.execute("CREATE INDEX IF NOT EXISTS idx_objects_kod_obce ON objects(kod_obce)")
    conn.execute(
        "CREATE INDEX IF NOT EXISTS idx_objects_kod_stavebni ON objects(kod_stavebni_objekt)"
    )
    conn.commit()


@contextmanager
def get_connection():
    db_path = _resolve_path(settings.database_url)
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    _ensure_schema(conn)
    try:
        yield conn
    finally:
        conn.close()


def load_objects(conn: sqlite3.Connection, kod_obce: str) -> list[ObjectRecord]:
    cur = conn.execute("SELECT * FROM objects WHERE kod_obce = ?", (kod_obce,))
    rows = cur.fetchall()
    return [ObjectRecord.from_row(row) for row in rows]


def replace_objects(conn: sqlite3.Connection, kod_obce: str, objects: Iterable[ObjectRecord]) -> None:
    conn.execute("DELETE FROM objects WHERE kod_obce = ?", (kod_obce,))
    for obj in objects:
        conn.execute(
            """
            INSERT INTO objects (
                kod_obce, kod_stavebni_objekt, typ, byty_odhad, letaky, lon, lat,
                ulice, cp_ce, cast_obce, psc, nejiste
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                kod_obce,
                obj.kod_stavebni_objekt,
                obj.typ,
                obj.byty_odhad,
                obj.letaky,
                obj.lon,
                obj.lat,
                obj.ulice,
                obj.cp_ce,
                obj.cast_obce,
                obj.psc,
                obj.nejiste,
            ),
        )
    conn.commit()


def get_cache(conn: sqlite3.Connection, kod_obce: str) -> MunicipalityCache | None:
    cur = conn.execute("SELECT * FROM municipality_cache WHERE kod_obce = ?", (kod_obce,))
    row = cur.fetchone()
    if not row:
        return None
    return MunicipalityCache.from_row(row)


def upsert_cache(conn: sqlite3.Connection, cache: MunicipalityCache) -> None:
    conn.execute(
        """
        INSERT INTO municipality_cache (kod_obce, name, created_at, raw_source)
        VALUES (?, ?, ?, ?)
        ON CONFLICT(kod_obce) DO UPDATE SET
            name = excluded.name,
            created_at = excluded.created_at,
            raw_source = excluded.raw_source
        """,
        (cache.kod_obce, cache.name, cache.created_at_iso, cache.raw_source),
    )
    conn.commit()

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any


@dataclass
class MunicipalityCache:
    kod_obce: str
    name: str
    created_at: datetime
    raw_source: str | None = None

    @property
    def created_at_iso(self) -> str:
        return self.created_at.isoformat()

    @staticmethod
    def from_row(row: Any) -> "MunicipalityCache":
        created = datetime.fromisoformat(row["created_at"]) if row["created_at"] else datetime.utcnow()
        return MunicipalityCache(
            kod_obce=row["kod_obce"],
            name=row["name"],
            created_at=created,
            raw_source=row["raw_source"],
        )


@dataclass
class ObjectRecord:
    kod_obce: str
    kod_stavebni_objekt: str
    typ: str
    byty_odhad: int
    letaky: int
    lon: float | None
    lat: float | None
    ulice: str | None
    cp_ce: str | None
    cast_obce: str | None
    psc: str | None
    nejiste: int = 0

    @staticmethod
    def from_row(row: Any) -> "ObjectRecord":
        return ObjectRecord(
            kod_obce=row["kod_obce"],
            kod_stavebni_objekt=row["kod_stavebni_objekt"],
            typ=row["typ"],
            byty_odhad=row["byty_odhad"],
            letaky=row["letaky"],
            lon=row["lon"],
            lat=row["lat"],
            ulice=row["ulice"],
            cp_ce=row["cp_ce"],
            cast_obce=row["cast_obce"],
            psc=row["psc"],
            nejiste=row["nejiste"],
        )

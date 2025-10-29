from __future__ import annotations

import csv
import io
import json
import logging
import urllib.error
import urllib.request
from collections import defaultdict
from dataclasses import dataclass
from typing import Iterable, List

from .config import get_settings

logger = logging.getLogger(__name__)

settings = get_settings()


@dataclass
class RuianRecord:
    kod_stavebni_objekt: str
    typ_budovy: str | None
    lon: float | None
    lat: float | None
    cislo_domovni: str | None
    ulice: str | None
    cast_obce: str | None
    obec: str | None
    psc: str | None


async def search_municipality(query: str) -> List[dict[str, str]]:
    q = query.strip()
    if not q:
        return []

    if settings.ruian_source_url:
        url = f"{settings.ruian_source_url.rstrip('/')}/search?municipality={urllib.parse.quote(q)}"
        try:
            with urllib.request.urlopen(url, timeout=10) as response:
                payload = json.loads(response.read().decode("utf-8"))
                return [
                    {"name": item.get("name", ""), "kod_obce": str(item.get("kod_obce"))}
                    for item in payload.get("results", [])
                    if item.get("kod_obce")
                ]
        except (urllib.error.URLError, ValueError) as exc:  # pragma: no cover - network fallback
            logger.warning("RUIAN search failed: %s", exc)

    samples = [
        {"name": "Jihlava", "kod_obce": "586846"},
        {"name": "Brno", "kod_obce": "582786"},
        {"name": "Praha", "kod_obce": "554782"},
    ]
    q_lower = q.lower()
    return [item for item in samples if q_lower in item["name"].lower()]


async def download_ruian_data(kod_obce: str) -> list[dict[str, str]]:
    if settings.ruian_source_url:
        url = f"{settings.ruian_source_url.rstrip('/')}/municipality/{kod_obce}"
        try:
            with urllib.request.urlopen(url, timeout=20) as response:
                content_type = response.headers.get("content-type", "")
                text = response.read().decode("utf-8")
                if "json" in content_type:
                    return json.loads(text)
                return list(parse_csv(text.splitlines()))
        except (urllib.error.URLError, ValueError) as exc:  # pragma: no cover
            logger.warning("Failed to download RUIAN data: %s", exc)
    return list(load_sample_data())


def parse_csv(lines: Iterable[str]) -> Iterable[dict[str, str]]:
    reader = csv.DictReader(lines, delimiter=";")
    for row in reader:
        yield row


def load_sample_data() -> Iterable[dict[str, str]]:
    sample_path = settings.project_root / "backend" / "data" / "sample_ruian.csv"
    with open(sample_path, "r", encoding="utf-8") as fh:
        yield from parse_csv(fh)


def coalesce_record(raw: dict[str, str]) -> RuianRecord:
    lon = raw.get("Longitude") or raw.get("X") or raw.get("lon")
    lat = raw.get("Latitude") or raw.get("Y") or raw.get("lat")
    try:
        lon_f = float(lon) if lon else None
        lat_f = float(lat) if lat else None
    except ValueError:
        lon_f = lat_f = None

    return RuianRecord(
        kod_stavebni_objekt=str(raw.get("KodStavebniObjekt") or raw.get("KodSO")),
        typ_budovy=(raw.get("TypBudovy") or raw.get("DruhStavby") or None),
        lon=lon_f,
        lat=lat_f,
        cislo_domovni=raw.get("CisloDomovni") or raw.get("CisloPopisne") or raw.get("CisloEvidencni"),
        ulice=raw.get("Ulice"),
        cast_obce=raw.get("CastObce"),
        obec=raw.get("Obec"),
        psc=raw.get("PSC"),
    )


def aggregate_records(records: Iterable[dict[str, str]]) -> list[RuianRecord]:
    aggregated: dict[str, list[RuianRecord]] = defaultdict(list)
    for raw in records:
        record = coalesce_record(raw)
        if not record.kod_stavebni_objekt:
            continue
        aggregated[record.kod_stavebni_objekt].append(record)
    result: list[RuianRecord] = []
    for items in aggregated.values():
        result.extend(items)
    return result


def serialize_records(records: Iterable[RuianRecord]) -> str:
    return json.dumps([record.__dict__ for record in records], ensure_ascii=False)


def deserialize_records(data: str) -> list[RuianRecord]:
    payload = json.loads(data)
    return [RuianRecord(**item) for item in payload]


def records_from_dicts(rows: Iterable[dict[str, str]]) -> list[RuianRecord]:
    return [coalesce_record(row) for row in rows if row.get("KodStavebniObjekt") or row.get("KodSO")]


def merge_uploaded_file(content: bytes) -> List[dict[str, str]]:
    with io.StringIO(content.decode("utf-8")) as fh:
        return list(parse_csv(fh))

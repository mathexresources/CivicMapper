from __future__ import annotations

from collections import defaultdict
from typing import Iterable, List

from ..models import ObjectRecord
from ..ruian import RuianRecord


class PlannerService:
    @staticmethod
    def classify(records: Iterable[RuianRecord], kod_obce: str) -> List[ObjectRecord]:
        grouped: dict[str, list[RuianRecord]] = defaultdict(list)
        for record in records:
            grouped[record.kod_stavebni_objekt].append(record)

        results: list[ObjectRecord] = []
        for kod_so, group in grouped.items():
            typ = PlannerService._determine_type(group)
            byty, nejiste = PlannerService._estimate_units(group, typ)
            letaky = PlannerService._estimate_leaflets(typ, byty)
            for entry in group:
                results.append(
                    ObjectRecord(
                        kod_obce=kod_obce,
                        kod_stavebni_objekt=kod_so,
                        typ=typ,
                        byty_odhad=byty,
                        letaky=letaky,
                        lon=entry.lon,
                        lat=entry.lat,
                        ulice=entry.ulice,
                        cp_ce=entry.cislo_domovni,
                        cast_obce=entry.cast_obce,
                        psc=entry.psc,
                        nejiste=1 if nejiste else 0,
                    )
                )
        return results

    @staticmethod
    def _determine_type(records: list[RuianRecord]) -> str:
        for record in records:
            if record.typ_budovy and "byt" in record.typ_budovy.lower():
                return "BD"
        return "BD" if len(records) > 1 else "RD"

    @staticmethod
    def _estimate_units(records: list[RuianRecord], typ: str) -> tuple[int, bool]:
        if typ == "RD":
            return 1, False
        count = len(records)
        nejiste = count > 100
        return (min(count, 100), nejiste)

    @staticmethod
    def _estimate_leaflets(typ: str, byty: int) -> int:
        if typ == "RD":
            return 1
        return byty

    @staticmethod
    def to_geojson(objects: List[ObjectRecord]) -> dict:
        features = []
        for obj in objects:
            geometry = {
                "type": "Point",
                "coordinates": [obj.lon, obj.lat] if obj.lon is not None and obj.lat is not None else None,
            }
            properties = {
                "id_obj": obj.kod_stavebni_objekt,
                "typ": obj.typ,
                "byty_odhad": obj.byty_odhad,
                "letaky": obj.letaky,
                "ulice": obj.ulice,
                "cp_ce": obj.cp_ce,
                "cast_obce": obj.cast_obce,
                "psc": obj.psc,
                "doporuceni": PlannerService._recommendations(obj.typ),
                "nejiste": bool(obj.nejiste),
            }
            if geometry["coordinates"] is None:
                properties["warnings"] = ["Chybí souřadnice"]
            features.append({"type": "Feature", "geometry": geometry, "properties": properties})
        return {"type": "FeatureCollection", "features": features}

    @staticmethod
    def _recommendations(typ: str) -> list[str]:
        if typ == "RD":
            return ["Schránka"]
        return ["Vchodové nástěnky", "Schránky u vchodu"]

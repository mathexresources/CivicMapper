from __future__ import annotations

import csv
import io
from xml.etree.ElementTree import Element, SubElement, tostring

from ..models import ObjectRecord


def export_csv(objects: list[ObjectRecord]) -> str:
    buffer = io.StringIO()
    writer = csv.writer(buffer, delimiter=";")
    writer.writerow([
        "KodStavebniObjekt",
        "Typ",
        "BytyOdhad",
        "Letaky",
        "Lon",
        "Lat",
        "Ulice",
        "Cislo",
        "CastObce",
        "PSC",
        "Nejiste",
    ])
    for obj in objects:
        writer.writerow(
            [
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
            ]
        )
    return buffer.getvalue()


def export_geojson(objects: list[ObjectRecord]) -> dict:
    from .planner import PlannerService

    return PlannerService.to_geojson(objects)


def export_kml(objects: list[ObjectRecord]) -> str:
    kml = Element("kml", xmlns="http://www.opengis.net/kml/2.2")
    document = SubElement(kml, "Document")
    for obj in objects:
        placemark = SubElement(document, "Placemark")
        SubElement(placemark, "name").text = f"{obj.typ} {obj.cp_ce or ''}"
        description = SubElement(placemark, "description")
        description.text = f"Letáky: {obj.letaky}, Byty: {obj.byty_odhad}"
        if obj.lon is not None and obj.lat is not None:
            point = SubElement(placemark, "Point")
            SubElement(point, "coordinates").text = f"{obj.lon},{obj.lat},0"
    return tostring(kml, encoding="utf-8").decode("utf-8")


def export_gpx(objects: list[ObjectRecord]) -> str:
    gpx = Element(
        "gpx",
        version="1.1",
        creator="Mikuláš Planner",
        xmlns="http://www.topografix.com/GPX/1/1",
    )
    for obj in objects:
        if obj.lon is None or obj.lat is None:
            continue
        wpt = SubElement(gpx, "wpt", lat=str(obj.lat), lon=str(obj.lon))
        SubElement(wpt, "name").text = f"{obj.typ} {obj.cp_ce or ''}"
        SubElement(wpt, "desc").text = f"Letáky: {obj.letaky}"
    return tostring(gpx, encoding="utf-8").decode("utf-8")

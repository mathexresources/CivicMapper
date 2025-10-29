from ..models import ObjectRecord
from ..services.exporters import export_csv, export_geojson, export_kml, export_gpx


def sample_object() -> ObjectRecord:
    return ObjectRecord(
        kod_obce="1",
        kod_stavebni_objekt="10",
        typ="BD",
        byty_odhad=3,
        letaky=3,
        lon=15.0,
        lat=49.0,
        ulice="Test",
        cp_ce="1",
        cast_obce="Test",
        psc="10000",
        nejiste=0,
    )


def test_export_csv():
    csv_content = export_csv([sample_object()])
    assert "KodStavebniObjekt" in csv_content
    assert "10" in csv_content


def test_export_geojson():
    geojson = export_geojson([sample_object()])
    assert geojson["type"] == "FeatureCollection"
    assert geojson["features"][0]["properties"]["letaky"] == 3


def test_export_kml():
    kml = export_kml([sample_object()])
    assert "Placemark" in kml


def test_export_gpx():
    gpx = export_gpx([sample_object()])
    assert "<gpx" in gpx

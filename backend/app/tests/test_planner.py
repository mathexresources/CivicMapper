from ..ruian import RuianRecord
from ..services.planner import PlannerService


def make_record(kod: str, typ: str | None = None):
    return RuianRecord(
        kod_stavebni_objekt=kod,
        typ_budovy=typ,
        lon=15.0,
        lat=49.0,
        cislo_domovni="1",
        ulice="Test",
        cast_obce="Test",
        obec="Test",
        psc="10000",
    )


def test_classify_rd():
    records = [make_record("1", "Rodinný dům")]
    objects = PlannerService.classify(records, "123")
    assert objects[0].typ == "RD"
    assert objects[0].byty_odhad == 1
    assert objects[0].letaky == 1


def test_classify_bd_by_count():
    records = [make_record("2"), make_record("2")]
    objects = PlannerService.classify(records, "123")
    assert all(obj.typ == "BD" for obj in objects)
    assert objects[0].byty_odhad == 2


def test_classify_bd_cap():
    records = [make_record("3") for _ in range(120)]
    objects = PlannerService.classify(records, "123")
    assert objects[0].byty_odhad == 100
    assert objects[0].nejiste == 1

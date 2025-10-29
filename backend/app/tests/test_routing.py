from ..services.routing import build_route


def test_greedy_route_order():
    points = [
        {"id": "a", "lon": 15.0, "lat": 49.0},
        {"id": "b", "lon": 15.001, "lat": 49.0},
        {"id": "c", "lon": 15.002, "lat": 49.0},
    ]
    route = build_route(points, engine="none", profile="foot")
    assert route["properties"]["order"][0] == "a"
    assert len(route["geometry"]["coordinates"]) == 3

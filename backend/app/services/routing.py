from __future__ import annotations

import json
import math
import urllib.error
import urllib.parse
import urllib.request
from typing import List

from ..config import get_settings

settings = get_settings()


def haversine_distance(lon1: float, lat1: float, lon2: float, lat2: float) -> float:
    r = 6371000
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return r * c


def route_with_osrm(points: List[dict], profile: str) -> dict:
    if not settings.osrm_base_url:
        raise RuntimeError("OSRM URL není nastaveno")
    coords = ";".join([f"{p['lon']},{p['lat']}" for p in points])
    url = f"{settings.osrm_base_url.rstrip('/')}/route/v1/{profile}/{coords}?overview=full&geometries=geojson"
    try:
        with urllib.request.urlopen(url, timeout=15) as response:
            data = json.loads(response.read().decode("utf-8"))
    except urllib.error.URLError as exc:
        raise RuntimeError(str(exc)) from exc
    route = data["routes"][0]
    return {
        "type": "Feature",
        "geometry": route["geometry"],
        "properties": {
            "distance_m": route.get("distance"),
            "duration_s": route.get("duration"),
            "order": [p["id"] for p in points],
        },
    }


def route_with_graphhopper(points: List[dict], profile: str) -> dict:
    if not settings.gh_base_url:
        raise RuntimeError("GraphHopper URL není nastaveno")
    url = f"{settings.gh_base_url.rstrip('/')}/route"
    payload = {
        "profile": profile,
        "points": [[p["lat"], p["lon"]] for p in points],
        "points_encoded": False,
    }
    data_bytes = json.dumps(payload).encode("utf-8")
    headers = {"Content-Type": "application/json"}
    if settings.gh_key:
        headers["Authorization"] = settings.gh_key
    request = urllib.request.Request(url, data=data_bytes, headers=headers)
    try:
        with urllib.request.urlopen(request, timeout=20) as response:
            data = json.loads(response.read().decode("utf-8"))
    except urllib.error.URLError as exc:
        raise RuntimeError(str(exc)) from exc
    path = data["paths"][0]
    return {
        "type": "Feature",
        "geometry": path["points"],
        "properties": {
            "distance_m": path.get("distance"),
            "duration_s": path.get("time", 0) / 1000,
            "order": [p["id"] for p in points],
        },
    }


def greedy_route(points: List[dict]) -> dict:
    if not points:
        return {
            "type": "Feature",
            "geometry": {"type": "LineString", "coordinates": []},
            "properties": {"distance_m": 0, "duration_s": 0, "order": []},
        }
    remaining = points.copy()
    order: list[dict] = []
    current = remaining.pop(0)
    order.append(current)
    while remaining:
        next_point = min(
            remaining,
            key=lambda p: haversine_distance(current["lon"], current["lat"], p["lon"], p["lat"]),
        )
        remaining.remove(next_point)
        order.append(next_point)
        current = next_point
    distance = 0.0
    for a, b in zip(order, order[1:]):
        distance += haversine_distance(a["lon"], a["lat"], b["lon"], b["lat"])
    duration = distance / 1.4
    return {
        "type": "Feature",
        "geometry": {
            "type": "LineString",
            "coordinates": [[p["lon"], p["lat"]] for p in order],
        },
        "properties": {
            "distance_m": distance,
            "duration_s": duration,
            "order": [p["id"] for p in order],
        },
    }


def build_route(points: List[dict], engine: str, profile: str) -> dict:
    if engine == "osrm":
        return route_with_osrm(points, profile)
    if engine == "graphhopper":
        return route_with_graphhopper(points, profile)
    return greedy_route(points)

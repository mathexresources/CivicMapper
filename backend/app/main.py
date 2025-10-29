from __future__ import annotations

import asyncio
from datetime import datetime
from typing import List

from fastapi import Depends, FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, PlainTextResponse

from .config import get_settings
from .database import (
    get_connection,
    get_cache,
    load_objects,
    replace_objects,
    upsert_cache,
)
from .models import MunicipalityCache
from .ruian import (
    deserialize_records,
    download_ruian_data,
    merge_uploaded_file,
    records_from_dicts,
    search_municipality,
    serialize_records,
)
from .schemas import PlanRequest, RouteRequest, SearchRequest
from .services.exporters import export_csv, export_geojson, export_gpx, export_kml
from .services.planner import PlannerService
from .services.routing import build_route

app = FastAPI(title="Mikuláš Planner")
settings = get_settings()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def get_db_conn():
    with get_connection() as conn:
        yield conn


@app.get("/api/status")
def status() -> dict:
    return {"status": "ok", "timestamp": datetime.utcnow().isoformat()}


@app.post("/api/search-municipality")
async def search(req: SearchRequest) -> List[dict[str, str]]:
    return await search_municipality(req.q)


async def _ensure_objects(conn, kod_obce: str):
    objects = load_objects(conn, kod_obce)
    if objects:
        return objects

    raw_records = await download_ruian_data(kod_obce)
    records = records_from_dicts(raw_records)
    objects = PlannerService.classify(records, kod_obce)
    replace_objects(conn, kod_obce, objects)

    cache_entry = MunicipalityCache(kod_obce=kod_obce, name=kod_obce, created_at=datetime.utcnow())
    cache_entry.raw_source = serialize_records(records)
    upsert_cache(conn, cache_entry)

    return load_objects(conn, kod_obce)


@app.post("/api/plan")
async def plan(req: PlanRequest, conn=Depends(get_db_conn)):
    objects = await _ensure_objects(conn, req.kod_obce)
    geojson = PlannerService.to_geojson(objects)
    return JSONResponse(content=geojson)


@app.post("/api/route")
async def route(req: RouteRequest):
    if not req.features:
        raise HTTPException(status_code=400, detail="Chybí body")
    points = [
        {"id": feature.id, "lon": feature.lon, "lat": feature.lat}
        for feature in req.features
    ]
    try:
        result = await asyncio.to_thread(build_route, points, req.engine, req.profile)
    except Exception as exc:
        if req.engine != "none":
            result = await asyncio.to_thread(build_route, points, "none", req.profile)
            return JSONResponse(status_code=503, content={"engine_error": str(exc), "fallback": result})
        raise HTTPException(status_code=503, detail=str(exc))
    return JSONResponse(content=result)


@app.get("/api/export.csv")
def export_csv_endpoint(kod_obce: str, conn=Depends(get_db_conn)):
    objects = load_objects(conn, kod_obce)
    content = export_csv(objects)
    return PlainTextResponse(content, media_type="text/csv; charset=utf-8")


@app.get("/api/export.geojson")
def export_geojson_endpoint(kod_obce: str, conn=Depends(get_db_conn)):
    objects = load_objects(conn, kod_obce)
    return JSONResponse(export_geojson(objects))


@app.get("/api/export.kml")
def export_kml_endpoint(kod_obce: str, conn=Depends(get_db_conn)):
    objects = load_objects(conn, kod_obce)
    content = export_kml(objects)
    return PlainTextResponse(content, media_type="application/vnd.google-earth.kml+xml")


@app.get("/api/export.gpx")
def export_gpx_endpoint(kod_obce: str, conn=Depends(get_db_conn)):
    objects = load_objects(conn, kod_obce)
    content = export_gpx(objects)
    return PlainTextResponse(content, media_type="application/gpx+xml")


@app.post("/api/ruian-upload")
async def ruian_upload(kod_obce: str, file: UploadFile = File(...), conn=Depends(get_db_conn)):
    data = await file.read()
    rows = merge_uploaded_file(data)
    records = records_from_dicts(rows)
    objects = PlannerService.classify(records, kod_obce)
    replace_objects(conn, kod_obce, objects)
    cache_entry = MunicipalityCache(kod_obce=kod_obce, name=kod_obce, created_at=datetime.utcnow())
    cache_entry.raw_source = serialize_records(records)
    upsert_cache(conn, cache_entry)
    return {"status": "ok", "records": len(objects)}


@app.get("/api/cache/{kod_obce}")
def cache_info(kod_obce: str, conn=Depends(get_db_conn)):
    cache_entry = get_cache(conn, kod_obce)
    if not cache_entry or not cache_entry.raw_source:
        raise HTTPException(status_code=404, detail="Cache nenalezena")
    records = deserialize_records(cache_entry.raw_source)
    return {"count": len(records), "created_at": cache_entry.created_at_iso}

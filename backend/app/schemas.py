from typing import Any, List
from pydantic import BaseModel, Field


class MunicipalityCandidate(BaseModel):
    name: str
    kod_obce: str


class SearchRequest(BaseModel):
    q: str


class PlanRequest(BaseModel):
    kod_obce: str
    routing: str | None = Field(default="none", pattern="^(osrm|graphhopper|none)$")


class FeatureGeometry(BaseModel):
    type: str
    coordinates: List[float]


class FeatureProperties(BaseModel):
    id_obj: str
    typ: str
    byty_odhad: int
    letaky: int
    ulice: str | None = None
    cp_ce: str | None = None
    cast_obce: str | None = None
    psc: str | None = None
    doporuceni: List[str]
    nejiste: bool = False


class Feature(BaseModel):
    type: str = "Feature"
    geometry: FeatureGeometry
    properties: FeatureProperties


class PlanResponse(BaseModel):
    type: str = "FeatureCollection"
    features: List[Feature]


class RouteFeature(BaseModel):
    id: str
    lon: float
    lat: float


class RouteRequest(BaseModel):
    features: List[RouteFeature]
    profile: str = Field(default="foot", pattern="^(foot|car)$")
    engine: str = Field(default="none", pattern="^(osrm|graphhopper|none)$")


class RouteResponse(BaseModel):
    type: str
    geometry: FeatureGeometry
    properties: dict[str, Any]

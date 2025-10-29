# Mikuláš Planner

Webový nástroj pro plánování roznosu letáků pro Mikuláše v obcích ČR. Projekt kombinuje FastAPI backend, který pracuje s daty RÚIAN, a frontend postavený na Reactu a Leafletu.

## Funkce
- Vyhledání obce, stažení a uložení adresních míst z RÚIAN.
- Heuristická klasifikace staveb na RD/BD, odhad počtu bytů, výpočet potřebných letáků.
- Mapová vizualizace, filtrace a statistiky.
- Návrh tras pomocí OSRM/GraphHopper nebo fallback heuristiky.
- Export dat do CSV, GeoJSON, KML a GPX.
- Možnost ručního nahrání RÚIAN CSV.

## Rychlý start

### Požadavky
- Docker a Docker Compose

### Spuštění
```bash
docker compose up --build
```
Backend poběží na `http://localhost:8000`, frontend na `http://localhost:5173`.

### Konfigurace
Zkopírujte `.env.example` na `.env` a upravte hodnoty:

- `RUIAN_SOURCE_URL` – volitelný vlastní endpoint pro stahování dat.
- `OSRM_BASE_URL`, `GH_BASE_URL`, `GH_KEY` – externí routing služby.
- `TILE_STYLE_URL` – URL stylu MapLibre kompatibilních dlaždic.

### Backend API
- `POST /api/search-municipality` – vyhledání obce.
- `POST /api/plan` – vytvoření plánu a uložení do cache.
- `POST /api/route` – výpočet trasy.
- `POST /api/ruian-upload` – ruční import CSV.
- `GET /api/export.(csv|geojson|kml|gpx)` – export.
- `GET /api/status` – healthcheck.

Příklady:
```bash
curl -X POST http://localhost:8000/api/search-municipality \
  -H 'Content-Type: application/json' \
  -d '{"q": "Jihlava"}'

curl -X POST http://localhost:8000/api/plan \
  -H 'Content-Type: application/json' \
  -d '{"kod_obce": "586846", "routing": "none"}'
```

### Testy
```bash
cd backend
pytest
```

### Právní poznámky
Projekt pracuje pouze s veřejně dostupnými daty RÚIAN. Nevyužívá osobní údaje ani neodvozuje přítomnost dětí v objektech. Odhad počtu bytů je heuristický a může být nepřesný.

### Datové limity
Pro velká města doporučujeme spuštění backendu s dostatečnou pamětí a časovým limitem pro stahování RÚIAN dat. Interní SQLite cache uchovává poslední načtená data dle kódu obce.

## Struktura
```
backend/    FastAPI aplikace, business logika, testy
frontend/   Vite + React aplikace
backend/data/sample_ruian.csv  ukázkový CSV soubor pro testování
```

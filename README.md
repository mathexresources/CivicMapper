### 🧭 Popis

**CivicMapper** je webová aplikace pro načítání, analýzu a vizualizaci dat z RÚIAN (Registr územní identifikace, adres a nemovitostí).
Umožňuje rychle zjistit počet domů v libovolné obci, odlišit rodinné a bytové domy, odhadnout počet bytů, připravit exporty pro další zpracování a navrhnout optimální trasy pro roznos letáků, sčítání nebo jiné terénní akce.

Původně vyvinuto pro **mikulášské obchůzky**, ale díky modulární architektuře lze použít pro:

* doručování letáků nebo poštovních zásilek
* krizové plánování
* komunitní mapování
* územní analýzy a vizualizace

---

### ⚙️ Funkce

* Vyhledání obce podle názvu
* Stažení dat o všech stavbách z RÚIAN (adresní místa, stavební objekty)
* Rozlišení typu: rodinný dům / bytový dům
* Odhad počtu bytů podle sdílených adresních míst
* Generování doporučení pro doručovací body
* Export do CSV, GeoJSON, KML, GPX
* Návrh tras pomocí OSRM / GraphHopper (volitelně)
* Webové mapové rozhraní (Leaflet + React)
* Lokální cache pro rychlé opakované použití (SQLite)
* Dockerized deployment

---

### 🧩 Architektura

**Backend:** Python + FastAPI
**Frontend:** React + TypeScript + Vite + Leaflet
**Databáze:** SQLite (cache)
**Routing engines:** OSRM / GraphHopper (volitelné přes .env)
**Mapové podklady:** OSM / OpenMapTiles (bez API klíče)

---

### 🗺️ API

| Endpoint                   | Metoda | Popis                               |
| -------------------------- | ------ | ----------------------------------- |
| `/api/search-municipality` | POST   | Vyhledá obec podle názvu            |
| `/api/plan`                | POST   | Vygeneruje plán domů a typy objektů |
| `/api/route`               | POST   | Navrhne trasu dle zvoleného engine  |
| `/api/export.csv`          | GET    | Export do CSV                       |
| `/api/export.geojson`      | GET    | Export do GeoJSON                   |
| `/api/export.kml`          | GET    | Export do KML                       |
| `/api/export.gpx`          | GET    | Export do GPX                       |
| `/api/status`              | GET    | Healthcheck                         |

---

### 🧰 Instalace

#### 1. Klonování

```bash
git clone https://github.com/<user>/CivicMapper.git
cd CivicMapper
```

#### 2. Konfigurace

Zkopíruj `.env.example` → `.env` a uprav:

```env
RUIAN_SOURCE_URL=https://vdp.cuzk.cz/vdp/ruian/adresy/
OSRM_BASE_URL=https://router.project-osrm.org
GH_BASE_URL=
GH_KEY=
TILE_STYLE_URL=https://basemaps.cartocdn.com/light_all/{z}/{x}/{y}.png
```

#### 3. Spuštění (Docker)

```bash
docker-compose up --build
```

Frontend: [http://localhost:5173](http://localhost:5173)
Backend API: [http://localhost:8000](http://localhost:8000)

---

### 🧪 Testy

```bash
pytest tests/
```

Testují:

* Klasifikaci RD/BD
* Výpočet bytů
* Exportery (CSV/KML/GPX)
* Routing fallback algoritmus

---

### 📤 Exportované formáty

* **CSV:** tabulka adres, typ objektu, počet bytů
* **GeoJSON:** pro QGIS / webové mapy
* **KML:** pro Google Earth / Mapy.cz
* **GPX:** pro navigace (OsmAnd, Locus, apod.)

---

### ⚖️ Právní poznámky

* Používá pouze **veřejná data z RÚIAN**.
* Neobsahuje a nesmí obsahovat žádné osobní údaje.
* Nepokouší se odhadovat přítomnost osob nebo dětí.
* Dodržuje GDPR a zákon č. 110/2019 Sb. o zpracování osobních údajů.

---

### 📦 Struktura projektu

```
CivicMapper/
├── backend/
│   ├── main.py
│   ├── ruian_parser.py
│   ├── router_engine.py
│   ├── export/
│   └── db/
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   ├── pages/
│   │   └── api/
├── tests/
├── docker-compose.yml
├── Dockerfile
├── .env.example
└── README.md
```

---

### 🔒 Licence

MIT License.
Použití dat RÚIAN podléhá licenčním podmínkám ČÚZK (Creative Commons CC BY 4.0).

---

Chceš, abych k tomu vytvořil i hotový obsah `README.md` souboru s markdown formátováním připravený k vložení do repozitáře (včetně odkazů, ikon a badge)?

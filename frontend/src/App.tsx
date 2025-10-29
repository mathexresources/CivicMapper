import { useEffect, useMemo, useState } from 'react';
import axios from 'axios';
import { MapContainer, TileLayer, Marker, Popup, Polyline } from 'react-leaflet';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';
import { usePlannerStore, Feature } from './store/usePlannerStore';

const markerIcons = {
  RD: new L.Icon({
    iconUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon.png',
    iconSize: [25, 41],
    iconAnchor: [12, 41],
    className: 'marker-rd'
  }),
  BD: new L.Icon({
    iconUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon-2x.png',
    iconSize: [25, 41],
    iconAnchor: [12, 41],
    className: 'marker-bd'
  })
};

const defaultCenter: [number, number] = [49.8038, 15.4749];

interface MunicipalityCandidate {
  name: string;
  kod_obce: string;
}

interface RouteFeatureInput {
  id: string;
  lon: number;
  lat: number;
}

function useStats(features: Feature[]) {
  return useMemo(() => {
    const total = features.length;
    const rd = features.filter((f) => f.typ === 'RD').length;
    const bd = features.filter((f) => f.typ === 'BD').length;
    const byty = features.reduce((acc, f) => acc + f.byty, 0);
    const letaky = features.reduce((acc, f) => acc + f.letaky, 0);
    const nejiste = features.filter((f) => f.nejiste).length;
    return { total, rd, bd, byty, letaky, nejiste, nejistePercent: total ? (nejiste / total) * 100 : 0 };
  }, [features]);
}

const App = () => {
  const [query, setQuery] = useState('');
  const [candidates, setCandidates] = useState<MunicipalityCandidate[]>([]);
  const [loadingPlan, setLoadingPlan] = useState(false);
  const [selectedForRoute, setSelectedForRoute] = useState<Feature[]>([]);
  const [routingEngine, setRoutingEngine] = useState<'osrm' | 'graphhopper' | 'none'>('none');
  const [routingProfile, setRoutingProfile] = useState<'foot' | 'car'>('foot');

  const municipality = usePlannerStore((state) => state.municipality);
  const features = usePlannerStore((state) => state.filtered);
  const setMunicipality = usePlannerStore((state) => state.setMunicipality);
  const setFeatures = usePlannerStore((state) => state.setFeatures);
  const updateFilters = usePlannerStore((state) => state.updateFilters);
  const applyFilters = usePlannerStore((state) => state.applyFilters);
  const route = usePlannerStore((state) => state.route);
  const setRoute = usePlannerStore((state) => state.setRoute);
  const stats = useStats(features);

  useEffect(() => {
    if (query.length < 3) {
      setCandidates([]);
      return;
    }
    const controller = new AbortController();
    axios
      .post<MunicipalityCandidate[]>('/api/search-municipality', { q: query }, { signal: controller.signal })
      .then((response) => setCandidates(response.data))
      .catch(() => setCandidates([]));
    return () => controller.abort();
  }, [query]);

  const selectMunicipality = (candidate: MunicipalityCandidate) => {
    setMunicipality({ name: candidate.name, kod: candidate.kod_obce });
    setQuery(candidate.name);
    setCandidates([]);
  };

  const loadPlan = async () => {
    if (!municipality) return;
    setLoadingPlan(true);
    try {
      const response = await axios.post('/api/plan', { kod_obce: municipality.kod, routing: routingEngine });
      const features = response.data.features
        .filter((f: any) => f.geometry.coordinates)
        .map((feature: any) => ({
          id: feature.properties.id_obj,
          typ: feature.properties.typ,
          byty: feature.properties.byty_odhad,
          letaky: feature.properties.letaky,
          lon: feature.geometry.coordinates[0],
          lat: feature.geometry.coordinates[1],
          address: `${feature.properties.ulice ?? ''} ${feature.properties.cp_ce ?? ''}`.trim(),
          castObce: feature.properties.cast_obce,
          psc: feature.properties.psc,
          doporuceni: feature.properties.doporuceni,
          nejiste: feature.properties.nejiste,
        })) as Feature[];
      setFeatures(features);
      setSelectedForRoute([]);
      setRoute(undefined);
    } finally {
      setLoadingPlan(false);
    }
  };

  const addToRoute = (feature: Feature) => {
    if (selectedForRoute.find((f) => f.id === feature.id)) return;
    setSelectedForRoute((prev) => [...prev, feature]);
  };

  const removeFromRoute = (id: string) => {
    setSelectedForRoute((prev) => prev.filter((f) => f.id !== id));
  };

  const moveRouteItem = (index: number, direction: -1 | 1) => {
    setSelectedForRoute((prev) => {
      const next = [...prev];
      const target = index + direction;
      if (target < 0 || target >= next.length) return next;
      const item = next[index];
      next.splice(index, 1);
      next.splice(target, 0, item);
      return next;
    });
  };

  const optimizeRoute = async () => {
    if (!selectedForRoute.length) return;
    const featuresPayload: RouteFeatureInput[] = selectedForRoute.map((f) => ({ id: f.id, lon: f.lon!, lat: f.lat! }));
    const response = await axios.post('/api/route', {
      features: featuresPayload,
      profile: routingProfile,
      engine: routingEngine,
    });
    const payload = response.data.fallback ? response.data.fallback : response.data;
    setRoute({
      geometry: payload.geometry,
      order: payload.properties.order,
      distance_m: payload.properties.distance_m,
      duration_s: payload.properties.duration_s,
    });
  };

  const exportUrl = (format: string) => (municipality ? `/api/export.${format}?kod_obce=${municipality.kod}` : '#');

  return (
    <div className="app-container">
      <div className="sidebar">
        <h1>Mikuláš Planner</h1>
        <label>
          Vyhledat obec
          <input
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Zadejte název obce"
            style={{ width: '100%', padding: '0.5rem', marginTop: '0.5rem' }}
          />
        </label>
        {candidates.length > 0 && (
          <ul>
            {candidates.map((candidate) => (
              <li key={candidate.kod_obce}>
                <button onClick={() => selectMunicipality(candidate)} style={{ width: '100%' }}>
                  {candidate.name}
                </button>
              </li>
            ))}
          </ul>
        )}
        <div className="controls">
          <button onClick={loadPlan} disabled={!municipality || loadingPlan}>
            {loadingPlan ? 'Načítám…' : 'Vytvořit plán'}
          </button>
          <select value={routingEngine} onChange={(e) => setRoutingEngine(e.target.value as any)}>
            <option value="none">Bez routingu</option>
            <option value="osrm">OSRM</option>
            <option value="graphhopper">GraphHopper</option>
          </select>
        </div>
        <div className="filters">
          <label>
            Typ:
            <select onChange={(e) => (updateFilters({ typ: e.target.value as any }), applyFilters())}>
              <option value="all">Vše</option>
              <option value="RD">Rodinné domy</option>
              <option value="BD">Bytové domy</option>
            </select>
          </label>
          <label>
            Byty od
            <input
              type="number"
              defaultValue={0}
              onBlur={(e) => {
                updateFilters({ minByty: Number(e.target.value) });
                applyFilters();
              }}
            />
          </label>
          <label>
            Byty do
            <input
              type="number"
              defaultValue={100}
              onBlur={(e) => {
                updateFilters({ maxByty: Number(e.target.value) });
                applyFilters();
              }}
            />
          </label>
          <label>
            <input
              type="checkbox"
              onChange={(e) => {
                updateFilters({ nejisteOnly: e.target.checked });
                applyFilters();
              }}
            />
            Jen nejisté
          </label>
        </div>
        <div className="stats">
          <h3>Statistiky</h3>
          <p>Domů celkem: {stats.total}</p>
          <p>RD: {stats.rd}</p>
          <p>BD: {stats.bd}</p>
          <p>Odhad bytů: {stats.byty}</p>
          <p>Doporučené letáky: {stats.letaky}</p>
          <p>Nejisté: {stats.nejiste} ({stats.nejistePercent.toFixed(1)} %)</p>
        </div>
        <div className="route-settings">
          <h3>Routing</h3>
          <label>
            Profil
            <select value={routingProfile} onChange={(e) => setRoutingProfile(e.target.value as any)}>
              <option value="foot">Chůze</option>
              <option value="car">Auto</option>
            </select>
          </label>
          <button onClick={optimizeRoute} disabled={!selectedForRoute.length}>
            Navrhnout trasu
          </button>
        </div>
        <div className="route-list">
          <h3>Vybrané body ({selectedForRoute.length})</h3>
          <ul>
            {selectedForRoute.map((item, index) => (
              <li key={item.id}>
                {item.address || item.id}{' '}
                <button onClick={() => moveRouteItem(index, -1)}>↑</button>
                <button onClick={() => moveRouteItem(index, 1)}>↓</button>
                <button onClick={() => removeFromRoute(item.id)}>Odebrat</button>
              </li>
            ))}
          </ul>
          {route && (
            <div>
              <h4>Souhrn trasy</h4>
              <p>Délka: {(route.distance_m / 1000).toFixed(2)} km</p>
              <p>Čas: {(route.duration_s / 60).toFixed(1)} min</p>
            </div>
          )}
        </div>
        <div className="exports">
          <h3>Export</h3>
          <a href={exportUrl('csv')} target="_blank" rel="noreferrer">
            CSV
          </a>{' '}
          <a href={exportUrl('geojson')} target="_blank" rel="noreferrer">
            GeoJSON
          </a>{' '}
          <a href={exportUrl('kml')} target="_blank" rel="noreferrer">
            KML
          </a>{' '}
          <a href={exportUrl('gpx')} target="_blank" rel="noreferrer">
            GPX
          </a>
        </div>
      </div>
      <div className="map-container">
        <MapContainer center={defaultCenter} zoom={13} style={{ height: '100%', width: '100%' }}>
          <TileLayer
            attribution='&copy; <a href="https://www.openmaptiles.org/">OpenMapTiles</a> &copy; <a href="https://www.openstreetmap.org/copyright">OSM</a>'
            url={
              import.meta.env.VITE_TILE_STYLE_URL ||
              'https://api.maptiler.com/maps/basic-v2/256/{z}/{x}/{y}.png?key=GetYourOwnKey'
            }
          />
          {features.map((feature) =>
            feature.lon && feature.lat ? (
              <Marker key={feature.id} position={[feature.lat, feature.lon]} icon={markerIcons[feature.typ]}>
                <Popup>
                  <strong>{feature.address}</strong>
                  <div>Typ: {feature.typ}</div>
                  <div>Odhad bytů: {feature.byty}</div>
                  <div>Letáky: {feature.letaky}</div>
                  <div>Doporučení: {feature.doporuceni.join(', ')}</div>
                  {feature.nejiste && <div style={{ color: 'red' }}>NEJISTÉ</div>}
                  <button onClick={() => addToRoute(feature)}>Přidat do trasy</button>
                </Popup>
              </Marker>
            ) : null
          )}
          {route && route.geometry.type === 'LineString' && (
            <Polyline positions={route.geometry.coordinates.map((c) => [c[1], c[0]])} color="red" />
          )}
        </MapContainer>
      </div>
    </div>
  );
};

export default App;

import create from 'zustand';

export type Feature = {
  id: string;
  typ: 'RD' | 'BD';
  byty: number;
  letaky: number;
  lon: number | null;
  lat: number | null;
  address: string;
  castObce?: string | null;
  psc?: string | null;
  doporuceni: string[];
  nejiste: boolean;
};

export type RouteResult = {
  geometry: { type: string; coordinates: [number, number][] };
  order: string[];
  distance_m: number;
  duration_s: number;
};

interface PlannerState {
  municipality?: { name: string; kod: string };
  features: Feature[];
  filtered: Feature[];
  route?: RouteResult;
  filters: {
    typ: 'all' | 'RD' | 'BD';
    nejisteOnly: boolean;
    minByty: number;
    maxByty: number;
  };
  setMunicipality: (m: { name: string; kod: string }) => void;
  setFeatures: (features: Feature[]) => void;
  setRoute: (route?: RouteResult) => void;
  updateFilters: (filters: Partial<PlannerState['filters']>) => void;
  applyFilters: () => void;
}

export const usePlannerStore = create<PlannerState>((set, get) => ({
  features: [],
  filtered: [],
  filters: {
    typ: 'all',
    nejisteOnly: false,
    minByty: 0,
    maxByty: 100,
  },
  setMunicipality: (m) => set({ municipality: m }),
  setFeatures: (features) => set({ features, filtered: features }),
  setRoute: (route) => set({ route }),
  updateFilters: (filters) => set({ filters: { ...get().filters, ...filters } }),
  applyFilters: () => {
    const { features, filters } = get();
    const result = features.filter((feature) => {
      if (filters.typ !== 'all' && feature.typ !== filters.typ) {
        return false;
      }
      if (filters.nejisteOnly && !feature.nejiste) {
        return false;
      }
      if (feature.byty < filters.minByty || feature.byty > filters.maxByty) {
        return false;
      }
      return true;
    });
    set({ filtered: result });
  },
}));

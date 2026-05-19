import { create } from 'zustand';

interface GraphState {
  selectedNode: any | null;
  setSelectedNode: (node: any | null) => void;
  searchQuery: string;
  setSearchQuery: (query: string) => void;
  filters: {
    communities: number[];
    minDegree: number;
  };
  setFilters: (filters: any) => void;
}

export const useGraphStore = create<GraphState>((set) => ({
  selectedNode: null,
  setSelectedNode: (node) => set({ selectedNode: node }),
  searchQuery: '',
  setSearchQuery: (query) => set({ searchQuery: query }),
  filters: {
    communities: [],
    minDegree: 0,
  },
  setFilters: (newFilters) => set((state) => ({ 
    filters: { ...state.filters, ...newFilters } 
  })),
}));

import { create } from 'zustand';
import { persist } from 'zustand/middleware';

interface SettingsState {
  retrieval: {
    topK: number;
    hybridAlpha: number;
    useReranker: boolean;
  };
  graph: {
    nodeSize: number;
    linkDistance: number;
    enablePhysics: boolean;
  };
  ui: {
    compactMode: boolean;
    showAnimations: boolean;
  };
  setRetrieval: (settings: any) => void;
  setGraph: (settings: any) => void;
  setUi: (settings: any) => void;
}

export const useSettingsStore = create<SettingsState>()(
  persist(
    (set) => ({
      retrieval: {
        topK: 5,
        hybridAlpha: 0.5,
        useReranker: true,
      },
      graph: {
        nodeSize: 6,
        linkDistance: 100,
        enablePhysics: true,
      },
      ui: {
        compactMode: false,
        showAnimations: true,
      },
      setRetrieval: (retrieval) => set((state) => ({ retrieval: { ...state.retrieval, ...retrieval } })),
      setGraph: (graph) => set((state) => ({ graph: { ...state.graph, ...graph } })),
      setUi: (ui) => set((state) => ({ ui: { ...state.ui, ...ui } })),
    }),
    { name: 'graph-rag-settings' }
  )
);

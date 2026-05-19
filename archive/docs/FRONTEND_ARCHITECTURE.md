# Graph RAG Platform - Frontend Architecture

This document outlines the complete production-ready frontend architecture for the Graph RAG platform, adhering to a clean, modern SaaS design with a focus on Neo4j graph analytics and highly modular UI components.

## 5. Recommended Dependency Installation Commands

```bash
# Initialize Vite Project
npm create vite@latest frontend -- --template react-ts
cd frontend

# Core Dependencies
npm install react-router-dom zustand @tanstack/react-query recharts framer-motion lucide-react

# Graph Visualization (Choosing React Force Graph for interactive 3D/2D graphs)
npm install react-force-graph-2d react-force-graph-3d d3-force

# UI / Styling / Tailwind & Shadcn setup
npm install -D tailwindcss postcss autoprefixer
npx tailwindcss init -p

# Utility libraries (often used with shadcn/ui)
npm install clsx tailwind-merge

# API Client
npm install axios
```

## 1. Full Frontend Folder Structure & 2. Every File Path & 3. Purpose of Each File

```text
src/
├── assets/
│   └── images/              # Static images, logos
├── components/
│   ├── common/              # Reusable generic UI elements (Buttons, Inputs, Cards)
│   │   ├── Card.tsx         # Base container for white modern SaaS cards
│   │   ├── SearchBar.tsx    # Global semantic search input
│   │   └── Layout.tsx       # Main app layout shell
│   ├── graph/               # Graph specific components
│   │   ├── GraphCanvas.tsx  # The main WebGL/Canvas graph rendering area
│   │   ├── GraphControls.tsx# Zoom, pan, physics controls, layout toggles
│   │   ├── NodeTooltip.tsx  # Hover information for graph nodes
│   │   ├── RelationLegend.tsx # Legend mapping edge colors to relation types
│   │   └── RelationTooltip.tsx# Hover info for edges
│   ├── navigation/          # Navigation components
│   │   ├── Navbar.tsx       # Top app bar (User profile, global actions)
│   │   └── Sidebar.tsx      # Left-side navigation menu
│   └── widgets/             # Domain-specific composite components
│       ├── ActivityTimeline.tsx # Timeline of graph updates or recent RAG queries
│       ├── CommunityCard.tsx    # Summary card for a specific Louvain community
│       ├── CommunityOverview.tsx# Grid/List of top communities
│       ├── EntityPanel.tsx      # Right-side drawer/panel for detailed entity view
│       ├── MetricsCharts.tsx    # Recharts based components for graph density, degree distribution
│       ├── QueryConsole.tsx     # Advanced Cypher/Semantic query input area
│       └── StatsCards.tsx       # High-level KPIs (Total Entities, Modularity Score)
├── hooks/
│   ├── useGraphData.ts      # React Query hook to fetch and cache graph topologies
│   ├── useEntityDetails.ts  # React Query hook for fetching specific node metadata
│   ├── useCommunities.ts    # React Query hook for Louvain community data
│   ├── useSearch.ts         # Hook handling semantic search debounce and API call
│   └── useWindowSize.ts     # Utility hook for responsive graph canvas sizing
├── layouts/
│   ├── DashboardLayout.tsx  # Layout containing Sidebar + Navbar + Content Area
│   └── FullScreenLayout.tsx # Layout for immersive graph exploration
├── lib/
│   ├── api.ts               # Axios instance configuration and interceptors
│   ├── utils.ts             # Tailwind class merging (clsx, twMerge)
│   └── formatters.ts        # Number/date formatting (e.g., modularity score to 2 decimals)
├── pages/
│   ├── Dashboard.tsx        # High-level metrics, recent activity, system overview
│   ├── GraphExplorer.tsx    # Main interactive graph workspace
│   ├── SemanticSearch.tsx   # Search interface with RAG results
│   ├── Communities.tsx      # Louvain communities analysis and hierarchy
│   ├── CentralEntities.tsx  # Page focusing on high PageRank/Degree nodes
│   ├── Documents.tsx        # Source files, parsing status, extraction metrics
│   ├── Monitoring.tsx       # System health, Neo4j connection status, API latency
│   └── Settings.tsx         # Platform config, LLM parameters, theme preferences
├── routes/
│   ├── index.tsx            # React Router configuration and route definitions
│   └── ProtectedRoute.tsx   # Wrapper for authenticated routes
├── services/
│   ├── graph.service.ts     # API calls related to graph structures (nodes, edges)
│   ├── search.service.ts    # API calls for vector/hybrid search
│   └── analytics.service.ts # API calls for Neo4j algorithms (Louvain, PageRank)
├── store/
│   ├── uiStore.ts           # Zustand store for sidebar state, active theme, panel visibility
│   ├── graphStore.ts        # Zustand store for selected node, active filters, physics state
│   └── authStore.ts         # Zustand store for user session and RBAC
├── styles/
│   ├── globals.css          # Tailwind imports, base CSS variables, custom utilities
│   └── theme.css            # White minimalist theme definitions (colors, shadows)
├── types/
│   ├── api.d.ts             # Interfaces for API responses
│   ├── graph.d.ts           # Graph interfaces (Node, Edge, Community)
│   └── index.d.ts           # Global type exports
├── App.tsx                  # Root component, Context Providers setup
└── main.tsx                 # React DOM rendering entry point
```

## 4. Starter Boilerplate Content

### `src/types/graph.d.ts`
```typescript
export interface GraphNode {
  id: string;
  label: string;
  group?: number | string; // Community ID
  properties: Record<string, any>;
  val?: number; // Node size/weight
}

export interface GraphEdge {
  source: string;
  target: string;
  type: string;
  properties?: Record<string, any>;
}

export interface GraphData {
  nodes: GraphNode[];
  links: GraphEdge[];
}
```

### `src/store/graphStore.ts`
```typescript
import { create } from 'zustand';
import { GraphNode } from '../types/graph';

interface GraphState {
  selectedNode: GraphNode | null;
  activeFilters: string[];
  isPanelOpen: boolean;
  setSelectedNode: (node: GraphNode | null) => void;
  toggleFilter: (filter: string) => void;
  setPanelOpen: (isOpen: boolean) => void;
}

export const useGraphStore = create<GraphState>((set) => ({
  selectedNode: null,
  activeFilters: [],
  isPanelOpen: false,
  setSelectedNode: (node) => set({ selectedNode: node, isPanelOpen: !!node }),
  toggleFilter: (filter) => set((state) => ({
    activeFilters: state.activeFilters.includes(filter)
      ? state.activeFilters.filter((f) => f !== filter)
      : [...state.activeFilters, filter],
  })),
  setPanelOpen: (isOpen) => set({ isPanelOpen: isOpen }),
}));
```

### `src/services/graph.service.ts`
```typescript
import { api } from '../lib/api';
import { GraphData } from '../types/graph';

export const GraphService = {
  getGraphTopology: async (limit = 1000): Promise<GraphData> => {
    const response = await api.get(`/api/v1/graph/topology?limit=${limit}`);
    return response.data;
  },
  
  getCommunityGraph: async (communityId: string): Promise<GraphData> => {
    const response = await api.get(`/api/v1/graph/communities/${communityId}`);
    return response.data;
  }
};
```

### `src/components/graph/GraphCanvas.tsx`
```typescript
import React, { useRef, useEffect, useState } from 'react';
import ForceGraph2D from 'react-force-graph-2d';
import { useGraphStore } from '../../store/graphStore';
import { GraphData, GraphNode } from '../../types/graph';
import { useWindowSize } from '../../hooks/useWindowSize';

interface GraphCanvasProps {
  data: GraphData;
}

export const GraphCanvas: React.FC<GraphCanvasProps> = ({ data }) => {
  const fgRef = useRef();
  const { width, height } = useWindowSize();
  const setSelectedNode = useGraphStore((state) => state.setSelectedNode);
  const [highlightNodes, setHighlightNodes] = useState(new Set());

  const handleNodeClick = (node: GraphNode) => {
    setSelectedNode(node);
    // Center camera on node (pseudo-code)
    // fgRef.current.centerAt(node.x, node.y, 1000);
    // fgRef.current.zoom(8, 2000);
  };

  return (
    <div className="w-full h-full bg-white rounded-xl shadow-sm border border-gray-100 overflow-hidden relative">
      <ForceGraph2D
        ref={fgRef}
        width={width ? width - 300 : 800} // Adjust for sidebar
        height={height ? height - 80 : 600} // Adjust for navbar
        graphData={data}
        nodeLabel="label"
        nodeAutoColorBy="group" // Color by Louvain community
        nodeRelSize={6}
        onNodeClick={handleNodeClick}
        linkColor={() => 'rgba(200, 200, 200, 0.4)'}
        linkDirectionalArrowLength={3.5}
        linkDirectionalArrowRelPos={1}
      />
    </div>
  );
};
```

### `src/layouts/DashboardLayout.tsx`
```typescript
import React from 'react';
import { Outlet } from 'react-router-dom';
import { Sidebar } from '../components/navigation/Sidebar';
import { Navbar } from '../components/navigation/Navbar';

export const DashboardLayout: React.FC = () => {
  return (
    <div className="flex h-screen bg-slate-50 font-sans text-slate-900">
      <Sidebar />
      <div className="flex flex-col flex-1 overflow-hidden">
        <Navbar />
        <main className="flex-1 overflow-x-hidden overflow-y-auto bg-slate-50 p-6">
          <div className="mx-auto max-w-7xl h-full">
            <Outlet />
          </div>
        </main>
      </div>
    </div>
  );
};
```

## 6. Architecture Explanation

The architecture follows a strict **feature-driven separation of concerns**, heavily reliant on modern React best practices.

*   **UI Layer (Shadcn/Tailwind):** Components are completely decoupled from business logic. Styling relies on a predefined Tailwind utility token set that ensures the "minimalist white SaaS" aesthetic.
*   **State Management Layer:** Divided into two distinct paradigms:
    *   **Server State (React Query):** Handles all asynchronous data fetching (Graph data, Entity details, RAG responses). This guarantees caching, background refetching, and reduces manual loading state management.
    *   **Client State (Zustand):** Handles purely UI-driven global state (e.g., currently selected node in the graph, whether the side panel is open, active graph filters).
*   **Service Layer:** Acts as an abstraction over HTTP requests. Components do not call `axios` directly; they call React Query hooks, which in turn call the Service layer.

## 7. State Management Strategy

1.  **Zustand for Global UI State:** Used because it lacks the boilerplate of Redux and provides a clean hook-based API. We separate stores logically (`uiStore`, `graphStore`, `authStore`) to prevent unnecessary re-renders across the app.
2.  **TanStack Query (React Query) for Server State:** Crucial for a RAG platform where querying Neo4j or Vector databases might take seconds. React Query handles the caching, so switching between the "Graph Explorer" and "Dashboard" does not re-fetch the entire multi-megabyte graph topology unless invalidated.
3.  **Local Component State (useState):** Strictly reserved for ephemeral UI states (e.g., toggling a dropdown, input field values before submission).

## 8. Graph Rendering Strategy

**Technology Choice:** `react-force-graph` (WebGL/Canvas) is recommended.
While standard DOM/SVG libraries (like generic D3) are great for small charts, Neo4j graphs easily scale into thousands of nodes.

*   **WebGL Canvas:** Renders nodes and edges on an HTML5 Canvas using WebGL, allowing smooth physics simulations for up to ~10,000 nodes without frame drops.
*   **Progressive Loading:** Do not fetch the entire Neo4j database. Initially load the most central entities (PageRank) or a specific Louvain community. Expand nodes on double-click.
*   **Styling:** Nodes are colored by their `group` (Louvain Community ID). Edges are thin and muted (`rgba(200, 200, 200, 0.4)`) to prevent visual clutter, highlighting only when a connected node is selected.

## 9. Scalability Recommendations

1.  **Pagination & Graph Expansion:** Never request `MATCH (n)-[r]-(m) RETURN n,r,m`. Always use limits and implement an "Expand Node" feature in the UI that fetches only 1-degree neighbors on demand.
2.  **WebWorkers for Graph Physics:** If using large datasets (5000+ nodes), offload the force-directed layout calculations to a WebWorker to prevent blocking the React main UI thread.
3.  **Code Splitting:** Use React `lazy()` and `Suspense` for routing. The GraphCanvas library is heavy; it should only load when the user navigates to the Graph Explorer page.
4.  **Debounced Search:** The Semantic Search bar must implement aggressive debouncing (e.g., 500ms) to prevent flooding the backend Vector/Hybrid search endpoints during typing.
5.  **Virtualization:** Lists like the "Documents" or "Central Entities" tables must use virtualization (`@tanstack/react-virtual`) if the list size exceeds 100 items.

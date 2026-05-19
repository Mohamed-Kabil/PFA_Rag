import { apiClient } from '../api/api-client';

export interface GraphMetrics {
  nodes: number;
  edges: number;
  total_nodes: number;
  total_edges: number;
  density: number;
  top_centrality: Record<string, number>;
  global_centrality?: Record<string, number>;
}

export interface Community {
  id: number;
  members: string[];
  size: number;
}

export interface MethodScore {
  chunks_count: number;
  cohesion: number;
  balance: number;
  score: number;
}

export interface ChunkingStats {
  total_chunks: number;
  available_methods: string[];
  current_method: string;
  method_scores: Record<string, MethodScore>;
  hierarchy: {
    document: string;
    total_chunks: number;
    sample_sub_chunks: string[];
  };
}

export interface AnalyticsData {
  entities: number;
  relations: number;
  communities: number;
  modularity: number;
}

export interface AgentDecision {
  action_taken: string;
  query_type: string;
  state: string;
  confidence_score: number;
  reward: number;
  routing_reason: string;
  q_values: Record<string, number>;
  policy_scores: Record<string, number>;
  decision_path: string[];
  q_update?: { old_value: number; new_value: number };
  retrieval_summary?: Record<string, unknown>;
}

export interface AgentState {
  epsilon: number;
  alpha: number;
  gamma: number;
  known_states: number;
  actions: string[];
  q_table: Record<string, number[]>;
  last_decisions: AgentDecision[];
}

export const systemService = {
  getHealth: async () => {
    const response = await apiClient.get('/');
    return response.data;
  },

  getChunkingStats: async (): Promise<ChunkingStats> => {
    const response = await apiClient.get('/chunking_stats');
    return response.data;
  },

  getChunkingTree: async () => {
    const response = await apiClient.get('/chunking_tree');
    return response.data;
  },

  getAgentState: async (): Promise<AgentState> => {
    const response = await apiClient.get('/agentic');
    return response.data;
  },

  getAnalytics: async (): Promise<AnalyticsData> => {
    const response = await apiClient.get('/analytics');
    return response.data;
  },
};

export const graphService = {
  getGraphMetrics: async (): Promise<GraphMetrics> => {
    const response = await apiClient.get('/analytics');
    return {
      total_nodes: response.data.entities,
      total_edges: response.data.relations,
      nodes: response.data.entities,
      edges: response.data.relations,
      density: 0,
      top_centrality: {},
    };
  },

  getCommunities: async (): Promise<Community[]> => {
    const response = await apiClient.get('/communities');
    return response.data.communities;
  },

  getFullGraph: async () => {
    const response = await apiClient.get('/graph_data', { timeout: 30000 });
    return response.data;
  },

  runLouvain: async () => {
    const response = await apiClient.get('/louvain');
    return response.data;
  },

  runCypher: async (query: string) => {
    const response = await apiClient.post('/cypher', { query }, { timeout: 30000 });
    return response.data as { keys: string[]; rows: Record<string, any>[]; count: number; is_graph: boolean };
  },

  getShortestPath: async (start: string, end: string) => {
    const response = await apiClient.get('/shortest_path', { params: { start, end } });
    return response.data as { status: string; path?: string[]; message?: string };
  },
};

export const searchService = {
  query: async (question: string) => {
    // LLM generation on CPU can take several minutes
    const response = await apiClient.post('/query', { question }, { timeout: 300000 });
    return response.data;
  },

  preview: async (question: string) => {
    const response = await apiClient.post('/query/analyze', { question });
    return response.data;
  },

  vectorialSearch: async (q: string, strategy = 'hybrid') => {
    const response = await apiClient.get('/vectorial', { params: { q, strategy }, timeout: 120000 });
    return response.data;
  },

  getPcaData: async () => {
    const response = await apiClient.get('/pca_data');
    return response.data;
  },

  pcaQuery: async (q: string, topK = 20) => {
    const response = await apiClient.get('/pca_query', { params: { q, top_k: topK } });
    return response.data as {
      query: string;
      results: { chunk_id: string; score: number; pca_x: number; pca_y: number; text: string }[];
    };
  }
};

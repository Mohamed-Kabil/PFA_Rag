import React, { useState, useRef } from 'react';
import { useQuery } from '@tanstack/react-query';
import { systemService, searchService } from '../../services/api-service';

import {
  ScatterChart, Scatter, XAxis, YAxis, ZAxis,
  CartesianGrid, Tooltip, Legend, ResponsiveContainer,
  BarChart, Bar, Cell,
} from 'recharts';
import { Layers, BarChart2, FileText, Database, Trophy, ChevronDown, ChevronRight, Search, X, Zap, GitBranch, Bot, CheckCircle2, XCircle } from 'lucide-react';

const PALETTE = ['#3b82f6','#a855f7','#10b981','#f59e0b','#ef4444','#06b6d4','#ec4899','#84cc16','#f97316','#8b5cf6'];

const RETRIEVAL_METHODS = [
  {
    id: 'bm25',
    name: 'BM25',
    fullName: 'Best Match 25',
    type: 'Sparse',
    Icon: Search,
    iconColor: 'text-orange-500',
    badgeClass: 'bg-orange-100 dark:bg-orange-900/40 text-orange-700 dark:text-orange-300',
    borderActive: 'border-orange-300 dark:border-orange-700',
    borderDefault: 'border-gray-100 dark:border-gray-800',
    bg: 'bg-orange-50 dark:bg-orange-900/10',
    barColor: 'bg-orange-400',
    description: 'Probabilistic keyword retrieval using Okapi BM25. Scores terms by TF-IDF with document-length normalization. Deterministic, fast, no embedding needed.',
    strengths: ['Exact keyword matches', 'No GPU required', 'Handles rare technical terms'],
    weaknesses: ['Misses semantic synonyms', 'Vocabulary gap on paraphrases'],
    speed: 92, precision: 72, recall: 65,
    strategy: 'bm25',
  },
  {
    id: 'semantic',
    name: 'Semantic',
    fullName: 'Dense Vector Search',
    type: 'Dense',
    Icon: Layers,
    iconColor: 'text-purple-500',
    badgeClass: 'bg-purple-100 dark:bg-purple-900/40 text-purple-700 dark:text-purple-300',
    borderActive: 'border-purple-300 dark:border-purple-700',
    borderDefault: 'border-gray-100 dark:border-gray-800',
    bg: 'bg-purple-50 dark:bg-purple-900/10',
    barColor: 'bg-purple-400',
    description: 'FAISS cosine similarity over paraphrase-multilingual-mpnet-base-v2 (768D). Captures conceptual meaning beyond keyword overlap.',
    strengths: ['Understands context & meaning', 'Language-agnostic (multilingual)', 'Handles paraphrases'],
    weaknesses: ['Higher latency than BM25', 'Can drift on domain jargon'],
    speed: 60, precision: 78, recall: 81,
    strategy: 'semantic',
  },
  {
    id: 'hybrid',
    name: 'Hybrid',
    fullName: 'BM25 + Semantic Fusion',
    type: 'Fusion',
    Icon: Zap,
    iconColor: 'text-blue-500',
    badgeClass: 'bg-blue-100 dark:bg-blue-900/40 text-blue-700 dark:text-blue-300',
    borderActive: 'border-blue-300 dark:border-blue-700',
    borderDefault: 'border-gray-100 dark:border-gray-800',
    bg: 'bg-blue-50 dark:bg-blue-900/10',
    barColor: 'bg-blue-400',
    description: 'Linear score fusion — α·BM25 + (1-α)·Semantic. Combines keyword precision with semantic recall. Default vectorial strategy in the pipeline.',
    strengths: ['Highest overall recall', 'Robust across query types', 'Complementary signal fusion'],
    weaknesses: ['2× retrieval latency', 'Requires α hyperparameter tuning'],
    speed: 50, precision: 84, recall: 87,
    strategy: 'hybrid',
    isDefault: true,
  },
  {
    id: 'graph',
    name: 'Graph',
    fullName: 'KG Traversal (Neo4j)',
    type: 'Structured',
    Icon: GitBranch,
    iconColor: 'text-green-500',
    badgeClass: 'bg-green-100 dark:bg-green-900/40 text-green-700 dark:text-green-300',
    borderActive: 'border-green-300 dark:border-green-700',
    borderDefault: 'border-gray-100 dark:border-gray-800',
    bg: 'bg-green-50 dark:bg-green-900/10',
    barColor: 'bg-green-400',
    description: 'Neo4j GDS knowledge graph traversal. Retrieves entity relationships, Louvain community context, and semantic paths between concepts.',
    strengths: ['Structured entity reasoning', 'Community & relationship context', 'Multi-hop inference'],
    weaknesses: ['Requires KG construction', 'Limited to indexed entities only'],
    speed: 35, precision: 69, recall: 58,
    strategy: null,
  },
  {
    id: 'agentic',
    name: 'Agentic',
    fullName: 'Q-Learning Router',
    type: 'Adaptive',
    Icon: Bot,
    iconColor: 'text-rose-500',
    badgeClass: 'bg-rose-100 dark:bg-rose-900/40 text-rose-700 dark:text-rose-300',
    borderActive: 'border-rose-300 dark:border-rose-700',
    borderDefault: 'border-gray-100 dark:border-gray-800',
    bg: 'bg-rose-50 dark:bg-rose-900/10',
    barColor: 'bg-rose-400',
    description: 'ε-greedy Q-Learning agent routes each query to Vector / Graph / Hybrid. Learns optimal policy from reward signals — improves with usage.',
    strengths: ['Per-query adaptive selection', 'Self-optimizing via RL', 'Maximizes retrieval reward'],
    weaknesses: ['Needs warm-up exploration', 'ε-greedy trade-off at startup'],
    speed: 55, precision: 86, recall: 89,
    strategy: null,
    isAgent: true,
  },
];

export const VectorialRAG: React.FC = () => {
  const [expandedNodes, setExpandedNodes] = useState<Record<string, boolean>>({});
  const toggleNode = (key: string) => setExpandedNodes(p => ({ ...p, [key]: !p[key] }));

  // PCA filter state
  const [pcaFilterQuery, setPcaFilterQuery] = useState('');
  const [pcaHighlights, setPcaHighlights] = useState<{ x: number; y: number; text: string; score: number }[]>([]);
  const [pcaFiltering, setPcaFiltering] = useState(false);
  const [minScore, setMinScore] = useState(0.5);
  const pcaInputRef = useRef<HTMLInputElement>(null);

  // Derived — only chunks above the similarity threshold
  const filteredHighlights = React.useMemo(
    () => pcaHighlights.filter(r => r.score >= minScore),
    [pcaHighlights, minScore]
  );

  const handlePcaFilter = async (q: string) => {
    if (!q.trim()) return;
    setPcaFiltering(true);
    try {
      const data = await searchService.pcaQuery(q, 20);
      setPcaHighlights(
        data.results
          .filter(r => r.pca_x != null && r.pca_y != null)
          .map(r => ({ x: +r.pca_x.toFixed(4), y: +r.pca_y.toFixed(4), text: r.text, score: r.score }))
      );
    } catch (e) {
      console.error(e);
    } finally {
      setPcaFiltering(false);
    }
  };

  const clearPcaFilter = () => {
    setPcaHighlights([]);
    setPcaFilterQuery('');
    if (pcaInputRef.current) pcaInputRef.current.value = '';
  };

  const { data: chunkingStats, isLoading: loadingChunks } = useQuery({
    queryKey: ['chunking-stats'],
    queryFn: systemService.getChunkingStats,
  });

  const { data: treeData, isLoading: loadingTree } = useQuery({
    queryKey: ['chunking-tree'],
    queryFn: systemService.getChunkingTree,
  });

  const { data: pcaData, isLoading: loadingPca } = useQuery({
    queryKey: ['pca-data'],
    queryFn: searchService.getPcaData,
  });

  const scatterSeries = React.useMemo(() => {
    if (!pcaData?.chunks) return [];
    const groups: Record<string, { x: number; y: number; text: string }[]> = {};
    const limited = (pcaData.chunks as any[]).filter((c) => c.pca_x != null).slice(0, 600);
    for (const c of limited) {
      const label = c.plot_label || 'Other';
      if (!groups[label]) groups[label] = [];
      groups[label].push({ x: +c.pca_x.toFixed(4), y: +c.pca_y.toFixed(4), text: (c.text || '').slice(0, 80) });
    }
    return Object.entries(groups).map(([name, data], i) => ({ name, data, color: PALETTE[i % PALETTE.length] }));
  }, [pcaData]);

  // Build sorted chart data from method_scores
  const evalRows = React.useMemo(() => {
    const s = chunkingStats?.method_scores;
    if (!s) return [];
    return Object.entries(s)
      .map(([name, v]) => ({ name, ...v }))
      .sort((a, b) => b.score - a.score);
  }, [chunkingStats]);

  const maxScore = evalRows[0]?.score ?? 1;

  return (
    <div className="space-y-8 max-w-7xl mx-auto pb-12">
      {/* ── Header ── */}
      <div>
        <h1 className="text-2xl font-bold text-gray-900 dark:text-white flex items-center gap-2">
          <Database className="text-blue-600" size={24} />
          Page 1 — Vectorial RAG
        </h1>
        <p className="text-gray-500 dark:text-gray-400 mt-1">
          Chunking pipeline · FAISS embeddings · PCA 2D visualization · Hybrid retrieval (BM25 + Semantic)
        </p>
      </div>

      {/* ── Section 1: Chunking ── */}
      <div className="bg-white dark:bg-gray-900 rounded-2xl border border-gray-200 dark:border-gray-800 shadow-sm overflow-hidden">
        <div className="px-6 py-4 border-b border-gray-100 dark:border-gray-800 flex items-center gap-2">
          <FileText className="text-blue-500" size={18} />
          <h2 className="font-bold text-gray-900 dark:text-white">1. Text Chunking</h2>
        </div>
        <div className="p-6 space-y-6">
          {/* Stats row */}
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
            <div className="p-4 bg-blue-50 dark:bg-blue-900/10 rounded-xl border border-blue-100 dark:border-blue-900/30">
              <div className="text-[10px] font-bold uppercase text-blue-500 mb-1">Total Chunks</div>
              <div className="text-3xl font-bold text-gray-900 dark:text-white">
                {loadingChunks ? '…' : chunkingStats?.total_chunks ?? 0}
              </div>
            </div>
            <div className="p-4 bg-purple-50 dark:bg-purple-900/10 rounded-xl border border-purple-100 dark:border-purple-900/30">
              <div className="text-[10px] font-bold uppercase text-purple-500 mb-1">Method Selected</div>
              <div className="text-xl font-bold text-gray-900 dark:text-white">
                {loadingChunks ? '…' : chunkingStats?.current_method ?? '—'}
              </div>
            </div>
            <div className="p-4 bg-green-50 dark:bg-green-900/10 rounded-xl border border-green-100 dark:border-green-900/30">
              <div className="text-[10px] font-bold uppercase text-green-500 mb-1">Source Document</div>
              <div className="text-sm font-bold text-gray-900 dark:text-white truncate">
                {loadingChunks ? '…' : chunkingStats?.hierarchy?.document ?? '—'}
              </div>
            </div>
          </div>

          {/* Hierarchical chunking tree */}
          <div>
            <div className="text-xs font-bold uppercase text-gray-400 mb-4">Hierarchical Chunking Tree (real corpus data)</div>
            {loadingTree ? (
              <div className="h-32 animate-pulse bg-gray-50 dark:bg-gray-800 rounded-xl" />
            ) : treeData ? (
              <div className="w-full">
                {/* Root node — centered */}
                <div className="flex justify-center">
                  <div className="px-4 py-2 bg-blue-600 text-white text-xs font-bold rounded-xl shadow flex items-center gap-2">
                    <FileText size={13} />
                    {treeData.document}
                  </div>
                </div>

                {/* Stem from root to crossbar */}
                <div className="flex justify-center">
                  <div className="w-px h-5 bg-gray-300 dark:bg-gray-600" />
                </div>

                {/* Crossbar + chunk columns */}
                <div className="relative">
                  {/* Horizontal crossbar: spans from center of col-1 to center of col-3 */}
                  <div className="absolute top-0 left-[16%] right-[16%] h-px bg-gray-300 dark:bg-gray-600" />

                  <div className="grid grid-cols-3 gap-3 pt-0">
                    {treeData.chunks?.map((chunk: any, ci: number) => {
                      const expanded = expandedNodes[chunk.id];
                      const preview = chunk.text.slice(0, 85) + (chunk.text.length > 85 ? '…' : '');
                      const visibleSubs = chunk.sub_chunks?.slice(0, 3) ?? [];
                      const hiddenCount = (chunk.sub_chunks?.length ?? 0) - visibleSubs.length;

                      return (
                        <div key={chunk.id} className="flex flex-col items-center">
                          {/* Stem from crossbar down to chunk box */}
                          <div className="w-px h-5 bg-gray-300 dark:bg-gray-600" />

                          {/* Parent chunk box */}
                          <div
                            className="w-full p-3 bg-white dark:bg-gray-900 border-2 border-blue-300 dark:border-blue-700 rounded-xl shadow-sm cursor-pointer hover:border-blue-500 transition-all group"
                            onClick={() => toggleNode(chunk.id)}
                            title={chunk.text}
                          >
                            <div className="flex items-center justify-between mb-1.5">
                              <span className="text-[9px] font-black text-blue-500 uppercase tracking-wider">
                                Chunk {ci + 1}
                              </span>
                              <span className="text-gray-400 group-hover:text-blue-500 transition-colors">
                                {expanded ? <ChevronDown size={11} /> : <ChevronRight size={11} />}
                              </span>
                            </div>
                            <p className="text-[9px] text-gray-600 dark:text-gray-400 leading-relaxed font-mono line-clamp-4">
                              {expanded ? chunk.text : preview}
                            </p>
                            <div className="mt-1.5 text-[8px] text-gray-300 dark:text-gray-600">
                              {chunk.text.length} chars · {chunk.sub_chunks?.length ?? 0} sub-chunks
                            </div>
                          </div>

                          {/* Stem from chunk down to sub-chunks */}
                          {visibleSubs.length > 0 && (
                            <div className="w-px h-3 bg-gray-200 dark:bg-gray-700" />
                          )}

                          {/* Sub-chunks — stacked vertically */}
                          <div className="w-full space-y-1.5">
                            {visibleSubs.map((sub: any, si: number) => {
                              const subKey = `${chunk.id}-${si}`;
                              const subExpanded = expandedNodes[subKey];
                              const subPreview = sub.text.slice(0, 60) + (sub.text.length > 60 ? '…' : '');
                              return (
                                <div
                                  key={si}
                                  className="w-full p-2 bg-gray-50 dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg cursor-pointer hover:border-purple-400 hover:bg-purple-50 dark:hover:bg-purple-900/10 transition-all group"
                                  onClick={() => toggleNode(subKey)}
                                  title={sub.text}
                                >
                                  <div className="flex items-center justify-between mb-0.5">
                                    <span className="text-[8px] font-black text-purple-400 uppercase tracking-wider">
                                      Sub {si + 1}
                                    </span>
                                    <span className="text-gray-300 group-hover:text-purple-400 transition-colors">
                                      {subExpanded ? <ChevronDown size={9} /> : <ChevronRight size={9} />}
                                    </span>
                                  </div>
                                  <p className="text-[8px] text-gray-500 dark:text-gray-400 leading-relaxed font-mono">
                                    {subExpanded ? sub.text : subPreview}
                                  </p>
                                </div>
                              );
                            })}
                            {hiddenCount > 0 && (
                              <div className="text-center text-[8px] text-gray-400 py-1 bg-gray-50 dark:bg-gray-800 rounded-lg border border-dashed border-gray-200 dark:border-gray-700">
                                +{hiddenCount} more sub-chunks
                              </div>
                            )}
                          </div>
                        </div>
                      );
                    })}
                  </div>
                </div>
              </div>
            ) : (
              <p className="text-xs text-gray-400 italic">Tree unavailable — restart the backend.</p>
            )}
          </div>
        </div>
      </div>

      {/* ── Section 2: PCA 2D ── */}
      <div className="bg-white dark:bg-gray-900 rounded-2xl border border-gray-200 dark:border-gray-800 shadow-sm overflow-hidden">
        <div className="px-6 py-4 border-b border-gray-100 dark:border-gray-800 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Layers className="text-purple-500" size={18} />
            <h2 className="font-bold text-gray-900 dark:text-white">2. Embedding Space — PCA 2D</h2>
          </div>
          {pcaData?.stats && (
            <span className="text-xs text-gray-400 font-medium">
              Variance retained: {((pcaData.stats.pca_total_2d_variance ?? 0) * 100).toFixed(1)}%
              &nbsp;·&nbsp;{pcaData.stats.chunk_count} chunks
              &nbsp;·&nbsp;{pcaData.stats.embedding_dimension}D → 2D
            </span>
          )}
        </div>
        <div className="p-6 space-y-4">
          {loadingPca ? (
            <div className="h-80 flex items-center justify-center text-gray-400 animate-pulse text-sm">
              Loading embeddings…
            </div>
          ) : scatterSeries.length > 0 ? (
            <>
              {/* Filter bar */}
              <form
                onSubmit={(e) => { e.preventDefault(); handlePcaFilter(pcaFilterQuery); }}
                className="flex gap-2 items-center"
              >
                <div className="relative flex-1">
                  <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" size={14} />
                  <input
                    ref={pcaInputRef}
                    type="text"
                    value={pcaFilterQuery}
                    onChange={(e) => setPcaFilterQuery(e.target.value)}
                    placeholder="Filter PCA — type a query to highlight nearest chunks…"
                    className="w-full pl-9 pr-4 py-2 text-sm bg-gray-50 dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500"
                  />
                </div>
                <button
                  type="submit"
                  disabled={pcaFiltering || !pcaFilterQuery.trim()}
                  className="px-4 py-2 bg-purple-600 hover:bg-purple-700 text-white rounded-lg text-sm font-medium disabled:opacity-50 flex items-center gap-1.5 transition-colors"
                >
                  {pcaFiltering
                    ? <div className="w-3.5 h-3.5 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                    : <Zap size={13} />}
                  Filter
                </button>
                {pcaHighlights.length > 0 && (
                  <button
                    type="button"
                    onClick={clearPcaFilter}
                    className="px-3 py-2 bg-gray-100 dark:bg-gray-800 hover:bg-gray-200 dark:hover:bg-gray-700 text-gray-600 dark:text-gray-300 rounded-lg text-sm font-medium flex items-center gap-1.5 transition-colors"
                  >
                    <X size={13} /> Clear
                  </button>
                )}
              </form>

              {/* Threshold slider — shown once a query has been run */}
              {pcaHighlights.length > 0 && (
                <div className="flex items-center gap-3 px-3 py-2 bg-gray-50 dark:bg-gray-800/60 rounded-lg border border-gray-200 dark:border-gray-700">
                  <span className="text-[11px] text-gray-500 dark:text-gray-400 shrink-0 font-medium">Min similarity</span>
                  <input
                    type="range"
                    min={0}
                    max={1}
                    step={0.05}
                    value={minScore}
                    onChange={(e) => setMinScore(+e.target.value)}
                    className="flex-1 accent-amber-500 h-1.5 cursor-pointer"
                  />
                  <span className="text-[11px] font-mono font-bold text-amber-600 dark:text-amber-400 w-8 text-right shrink-0">
                    {minScore.toFixed(2)}
                  </span>
                  <span className="text-[10px] text-gray-400 shrink-0">
                    {filteredHighlights.length}/{pcaHighlights.length} shown
                  </span>
                </div>
              )}

              {/* Highlight summary */}
              {pcaHighlights.length > 0 && (
                <div className="flex items-center gap-2 text-xs font-medium">
                  <span className="inline-block w-3 h-3 rounded-full bg-amber-400 border-2 border-amber-500" />
                  {filteredHighlights.length > 0 ? (
                    <span className="text-purple-600 dark:text-purple-400">
                      {filteredHighlights.length} chunk{filteredHighlights.length !== 1 ? 's' : ''} above {minScore.toFixed(2)} similarity highlighted
                      {filteredHighlights.length < pcaHighlights.length && (
                        <span className="text-gray-400 ml-1">
                          · {pcaHighlights.length - filteredHighlights.length} hidden below threshold
                        </span>
                      )}
                    </span>
                  ) : (
                    <span className="text-red-500">
                      No chunks above {minScore.toFixed(2)} — lower the threshold or try a more relevant query
                    </span>
                  )}
                </div>
              )}

              {/* Chart */}
              <div className="h-80 w-full">
                <ResponsiveContainer width="100%" height="100%">
                  <ScatterChart margin={{ top: 10, right: 20, bottom: 10, left: 0 }}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" opacity={0.3} />
                    <XAxis dataKey="x" type="number" name="PC1" tick={{ fontSize: 10 }} tickLine={false} axisLine={false} domain={['auto', 'auto']} label={{ value: 'PC1', position: 'insideBottomRight', offset: -5, fontSize: 11 }} />
                    <YAxis dataKey="y" type="number" name="PC2" tick={{ fontSize: 10 }} tickLine={false} axisLine={false} domain={['auto', 'auto']} label={{ value: 'PC2', angle: -90, position: 'insideLeft', fontSize: 11 }} />
                    <ZAxis range={[18, 18]} />
                    <Tooltip
                      cursor={{ strokeDasharray: '3 3' }}
                      content={({ payload }) => {
                        if (!payload?.length) return null;
                        const d = payload[0]?.payload as any;
                        return (
                          <div className="bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-700 rounded-lg p-3 shadow-lg max-w-xs text-xs">
                            <p className="text-gray-400 mb-1">PC1: {d?.x} · PC2: {d?.y}</p>
                            {d?.score != null && <p className="text-amber-500 font-bold mb-1">Similarity: {d.score.toFixed(4)}</p>}
                            <p className="text-gray-700 dark:text-gray-300 italic">"{d?.text}…"</p>
                          </div>
                        );
                      }}
                    />
                    <Legend wrapperStyle={{ fontSize: '11px', paddingTop: '12px' }} />
                    {/* Base series — dimmed when filter active */}
                    {scatterSeries.map((s) => (
                      <Scatter
                        key={s.name}
                        name={s.name}
                        data={s.data}
                        fill={s.color}
                        fillOpacity={filteredHighlights.length > 0 ? 0.12 : 0.75}
                      />
                    ))}
                    {/* Highlight overlay — only chunks above minScore threshold */}
                    {filteredHighlights.length > 0 && (
                      <Scatter
                        name="Query Match"
                        data={filteredHighlights}
                        fill="#f59e0b"
                        fillOpacity={1}
                        r={6}
                      />
                    )}
                  </ScatterChart>
                </ResponsiveContainer>
              </div>
              <p className="text-[10px] text-gray-400 text-center italic">
                Each point = one chunk · Color = chapter/cluster · Model: paraphrase-multilingual-mpnet-base-v2 · PCA 2D projection
              </p>
            </>
          ) : (
            <div className="h-80 flex items-center justify-center text-gray-400 text-sm italic">
              No PCA data available. Run the ingestion pipeline first.
            </div>
          )}
        </div>
      </div>

      {/* ── Section 3: Chunking Method Evaluation ── */}
      <div className="bg-white dark:bg-gray-900 rounded-2xl border border-gray-200 dark:border-gray-800 shadow-sm overflow-hidden">
        <div className="px-6 py-4 border-b border-gray-100 dark:border-gray-800 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <BarChart2 className="text-green-500" size={18} />
            <h2 className="font-bold text-gray-900 dark:text-white">3. Chunking Method Evaluation</h2>
          </div>
          <span className="text-[10px] text-gray-400 font-mono">
            Score = Cohesion × 2.0 + Balance × 0.5
          </span>
        </div>
        <p className="px-6 py-3 text-[11px] text-amber-700 dark:text-amber-400 bg-amber-50 dark:bg-amber-900/10 border-b border-amber-100 dark:border-amber-900/30 leading-relaxed">
          <span className="font-bold">Note:</span> Hierarchical chunking is used in the RAG pipeline for its overlap optimization, despite Fixed-Size achieving the highest composite score on this corpus sample.
        </p>
        {evalRows.length === 0 ? (
          <div className="p-10 text-center text-gray-400 text-sm italic">
            No evaluation data yet. Run <code className="bg-gray-100 dark:bg-gray-800 px-1 rounded">python -m backend.run_eval</code> once.
          </div>
        ) : (
          <div className="p-6 space-y-8">
            {/* ── Bar chart ── */}
            <div className="h-56">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={evalRows} margin={{ top: 4, right: 16, left: 0, bottom: 24 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
                  <XAxis dataKey="name" tick={{ fontSize: 10 }} interval={0} angle={-25} textAnchor="end" />
                  <YAxis tick={{ fontSize: 10 }} domain={[0, Math.ceil(maxScore * 10) / 10]} />
                  <Tooltip
                    content={({ payload }) => {
                      if (!payload?.length) return null;
                      const d = payload[0].payload as any;
                      return (
                        <div className="bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-700 rounded-lg p-3 shadow-lg text-xs space-y-1">
                          <p className="font-bold text-gray-800 dark:text-gray-200">{d.name}</p>
                          <p className="text-purple-500">Cohesion: {d.cohesion?.toFixed(3)}</p>
                          <p className="text-green-500">Balance: {d.balance?.toFixed(3)}</p>
                          <p className="font-bold text-blue-600">Score: {d.score?.toFixed(3)}</p>
                          <p className="text-gray-400">{d.chunks_count} chunks</p>
                        </div>
                      );
                    }}
                  />
                  <Bar dataKey="score" radius={[4, 4, 0, 0]}>
                    {evalRows.map((row, i) => (
                      <Cell
                        key={row.name}
                        fill={i === 0 ? '#f59e0b' : '#3b82f6'}
                        fillOpacity={i === 0 ? 1 : 0.65}
                      />
                    ))}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            </div>

            {/* ── Ranked rows ── */}
            <div className="space-y-3">
              {evalRows.map((row, i) => {
                const isWinner = i === 0;
                const isUsed = row.name === chunkingStats?.current_method;
                const cohPct = (row.cohesion / 1) * 100;
                const balPct = (row.balance / 1) * 100;
                const scorePct = (row.score / maxScore) * 100;
                return (
                  <div
                    key={row.name}
                    className={`p-4 rounded-xl border transition-all ${
                      isWinner
                        ? 'border-amber-300 dark:border-amber-700 bg-amber-50/60 dark:bg-amber-900/10'
                        : 'border-gray-100 dark:border-gray-800 bg-gray-50/40 dark:bg-gray-800/20'
                    }`}
                  >
                    <div className="flex items-center justify-between mb-3">
                      <div className="flex items-center gap-2">
                        <span className={`text-xs font-black w-5 text-center ${isWinner ? 'text-amber-500' : 'text-gray-400'}`}>
                          {isWinner ? '★' : `#${i + 1}`}
                        </span>
                        <span className="font-bold text-sm text-gray-800 dark:text-gray-200">{row.name}</span>
                        {isWinner && (
                          <span className="px-2 py-0.5 bg-amber-100 dark:bg-amber-900/40 text-amber-700 dark:text-amber-300 text-[10px] font-black rounded-full uppercase tracking-wider flex items-center gap-1">
                            <Trophy size={9} /> Best
                          </span>
                        )}
                        {isUsed && (
                          <span className="px-2 py-0.5 bg-blue-100 dark:bg-blue-900/40 text-blue-600 dark:text-blue-300 text-[10px] font-bold rounded-full">
                            ✓ In use
                          </span>
                        )}
                      </div>
                      <div className="flex items-center gap-4 text-[11px] font-mono">
                        <span className="text-purple-500">cohesion {row.cohesion?.toFixed(3)}</span>
                        <span className="text-green-500">balance {row.balance?.toFixed(3)}</span>
                        <span className={`font-bold ${isWinner ? 'text-amber-600' : 'text-blue-600'}`}>
                          score {row.score?.toFixed(3)}
                        </span>
                        <span className="text-gray-400">{row.chunks_count} chunks</span>
                      </div>
                    </div>

                    {/* Stacked mini-bars */}
                    <div className="grid grid-cols-3 gap-2">
                      {[
                        { label: 'Cohesion', pct: cohPct, color: 'bg-purple-400' },
                        { label: 'Balance',  pct: balPct, color: 'bg-green-400' },
                        { label: 'Score',    pct: scorePct, color: isWinner ? 'bg-amber-400' : 'bg-blue-400' },
                      ].map(({ label, pct, color }) => (
                        <div key={label}>
                          <div className="flex justify-between text-[9px] text-gray-400 mb-1">
                            <span>{label}</span>
                            <span>{pct.toFixed(0)}%</span>
                          </div>
                          <div className="h-1.5 bg-gray-100 dark:bg-gray-800 rounded-full overflow-hidden">
                            <div className={`h-full ${color} rounded-full transition-all`} style={{ width: `${pct}%` }} />
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        )}
      </div>
      {/* ── Section 4: Retrieval Methods Comparison ── */}
      <div className="bg-white dark:bg-gray-900 rounded-2xl border border-gray-200 dark:border-gray-800 shadow-sm overflow-hidden">
        <div className="px-6 py-4 border-b border-gray-100 dark:border-gray-800 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Search className="text-rose-500" size={18} />
            <h2 className="font-bold text-gray-900 dark:text-white">4. Retrieval Methods Comparison</h2>
          </div>
          <span className="text-[10px] text-gray-400">
            5 strategies · Agentic router selects the optimal one per query
          </span>
        </div>
        <div className="p-6">
          <div className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-3 gap-4">
            {RETRIEVAL_METHODS.map((m) => (
              <div
                key={m.id}
                className={`rounded-xl border-2 ${m.borderActive} ${m.bg} p-4 flex flex-col gap-3 transition-all`}
              >
                {/* Header */}
                <div className="flex items-start justify-between">
                  <div className="flex items-center gap-2">
                    <m.Icon className={m.iconColor} size={18} />
                    <div>
                      <div className="font-bold text-sm text-gray-900 dark:text-white leading-tight">{m.name}</div>
                      <div className="text-[10px] text-gray-400 leading-tight">{m.fullName}</div>
                    </div>
                  </div>
                  <div className="flex flex-col items-end gap-1">
                    <span className={`text-[9px] font-black uppercase tracking-wider px-2 py-0.5 rounded-full ${m.badgeClass}`}>
                      {m.type}
                    </span>
                    {m.isDefault && (
                      <span className="text-[9px] font-bold px-2 py-0.5 rounded-full bg-blue-100 dark:bg-blue-900/40 text-blue-600 dark:text-blue-300">
                        ✓ Default
                      </span>
                    )}
                    {m.isAgent && (
                      <span className="text-[9px] font-bold px-2 py-0.5 rounded-full bg-rose-100 dark:bg-rose-900/40 text-rose-600 dark:text-rose-300">
                        RL Agent
                      </span>
                    )}
                  </div>
                </div>

                {/* Description */}
                <p className="text-[11px] text-gray-600 dark:text-gray-400 leading-relaxed">
                  {m.description}
                </p>

                {/* Strengths / Weaknesses */}
                <div className="space-y-1">
                  {m.strengths.map((s) => (
                    <div key={s} className="flex items-start gap-1.5">
                      <CheckCircle2 className="text-green-500 mt-0.5 shrink-0" size={11} />
                      <span className="text-[10px] text-gray-600 dark:text-gray-400">{s}</span>
                    </div>
                  ))}
                  {m.weaknesses.map((w) => (
                    <div key={w} className="flex items-start gap-1.5">
                      <XCircle className="text-red-400 mt-0.5 shrink-0" size={11} />
                      <span className="text-[10px] text-gray-500 dark:text-gray-500">{w}</span>
                    </div>
                  ))}
                </div>

                {/* Performance bars */}
                <div className="space-y-1.5 pt-1 border-t border-gray-200/60 dark:border-gray-700/60">
                  {[
                    { label: 'Speed',     val: m.speed },
                    { label: 'Precision', val: m.precision },
                    { label: 'Recall',    val: m.recall },
                  ].map(({ label, val }) => (
                    <div key={label} className="flex items-center gap-2">
                      <span className="text-[9px] text-gray-400 w-14 shrink-0">{label}</span>
                      <div className="flex-1 h-1.5 bg-gray-200 dark:bg-gray-700 rounded-full overflow-hidden">
                        <div
                          className={`h-full ${m.barColor} rounded-full`}
                          style={{ width: `${val}%` }}
                        />
                      </div>
                      <span className="text-[9px] font-mono text-gray-500 w-7 text-right">{val}%</span>
                    </div>
                  ))}
                </div>
              </div>
            ))}
          </div>
          <p className="text-[10px] text-gray-400 mt-4 text-center italic">
            Performance values are indicative — estimated from corpus sample evaluation. Agentic combines all strategies adaptively.
          </p>
        </div>
      </div>

    </div>
  );
};

import React, { useState, useRef, useCallback, useMemo, useEffect } from 'react';
import { useQuery } from '@tanstack/react-query';
import { graphService, systemService } from '../../services/api-service';
import ForceGraph2D from 'react-force-graph-2d';
import {
  Users, Layers, Search, BarChart2, Database,
  RefreshCcw, Share2, GitBranch, ArrowRight,
  Zap, Star, Network, Target, Play, Terminal,
} from 'lucide-react';

const DEFAULT_CYPHER = `MATCH (e:Entity)
WHERE e.communityId IS NOT NULL
RETURN e.communityId AS community, collect(e.name)[0..10] AS members, count(e) AS size
ORDER BY size DESC
LIMIT 20`;

const COMMUNITY_COLORS = [
  '#3b82f6','#a855f7','#10b981','#f59e0b','#ef4444',
  '#06b6d4','#ec4899','#84cc16','#f97316','#8b5cf6',
];

type CypherResult = {
  keys: string[];
  rows: Record<string, any>[];
  count: number;
  is_graph: boolean;
};

function buildGraph(result: CypherResult) {
  const nodesMap = new Map<string, any>();
  const links: any[] = [];

  if (result.is_graph) {
    // Real Neo4j nodes + relationships
    for (const row of result.rows) {
      for (const val of Object.values(row)) {
        if (!val || typeof val !== 'object' || Array.isArray(val)) continue;
        if (val._neo4j_type === 'node') {
          if (!nodesMap.has(val._id)) {
            nodesMap.set(val._id, {
              id: val._id,
              label: val.name ?? val.id ?? val._id,
              community: val.communityId ?? 0,
              group: 'node',
            });
          }
        } else if (val._neo4j_type === 'relationship') {
          links.push({ source: val._start_id, target: val._end_id, label: val._rel_type });
        }
      }
    }
  } else {
    // Tabular results → hub-and-spoke: each row is a hub, array values are leaf nodes
    result.rows.forEach((row, i) => {
      const hubId = `hub_${i}`;
      // Pick the first scalar column as the hub label
      const hubLabel = result.keys
        .filter(k => !Array.isArray(row[k]))
        .map(k => String(row[k]))
        .join(' · ');

      nodesMap.set(hubId, { id: hubId, label: hubLabel, community: i, group: 'hub' });

      for (const k of result.keys) {
        const val = row[k];
        if (Array.isArray(val)) {
          (val as any[]).forEach((item) => {
            const leafId = `leaf_${String(item)}`;
            if (!nodesMap.has(leafId)) {
              nodesMap.set(leafId, { id: leafId, label: String(item), community: i, group: 'leaf' });
            }
            links.push({ source: hubId, target: leafId });
          });
        }
      }
    });
  }

  return { nodes: Array.from(nodesMap.values()), links };
}

export const Communities: React.FC = () => {
  const [searchQuery, setSearchQuery] = useState('');
  const [pathStart, setPathStart]     = useState('');
  const [pathEnd, setPathEnd]         = useState('');
  const [pathResult, setPathResult]   = useState<{ status: string; path?: string[]; message?: string } | null>(null);
  const [pathLoading, setPathLoading] = useState(false);

  const graphRef     = useRef<any>(null);
  const containerRef = useRef<HTMLDivElement>(null);

  const [cypherQuery,   setCypherQuery]   = useState(DEFAULT_CYPHER);
  const [cypherResult,  setCypherResult]  = useState<CypherResult | null>(null);
  const [cypherError,   setCypherError]   = useState<string | null>(null);
  const [cypherLoading, setCypherLoading] = useState(false);
  const [graphWidth,    setGraphWidth]    = useState(0);
  const [runId,         setRunId]         = useState(0);

  const handleRunCypher = async () => {
    if (!cypherQuery.trim()) return;
    setCypherLoading(true);
    setCypherError(null);
    setCypherResult(null);
    try {
      const result = await graphService.runCypher(cypherQuery);
      setRunId(id => id + 1);
      setCypherResult(result);
      // Measure container width for ForceGraph
      setTimeout(() => {
        if (containerRef.current) setGraphWidth(containerRef.current.clientWidth);
      }, 50);
    } catch (err: any) {
      setCypherError(err?.response?.data?.detail ?? err?.message ?? 'Query failed');
    } finally {
      setCypherLoading(false);
    }
  };

  const handleEngineStop = useCallback(() => {
    setTimeout(() => graphRef.current?.zoomToFit(400, 40), 50);
  }, []);

  // Strengthen repulsion after each new query so nodes spread out
  useEffect(() => {
    if (!graphRef.current || runId === 0) return;
    const fg = graphRef.current;
    fg.d3Force('charge')?.strength(-600);
    fg.d3Force('link')?.distance((link: any) => link.source?.group === 'hub' || link.target?.group === 'hub' ? 250 : 120);
    fg.d3ReheatSimulation();
  }, [runId]);

  const cypherGraphData = useMemo(() => {
    if (!cypherResult || cypherResult.count === 0) return null;
    return buildGraph(cypherResult);
  }, [cypherResult]);

  const { data: communities, isLoading, refetch, isFetching } = useQuery({
    queryKey: ['communities-detailed'],
    queryFn: graphService.getCommunities,
  });

  const { data: graphMetrics } = useQuery({
    queryKey: ['graph-metrics-global'],
    queryFn: () => graphService.getGraphMetrics(),
  });

  const { data: analytics } = useQuery({
    queryKey: ['analytics'],
    queryFn: systemService.getAnalytics,
  });

  const filteredCommunities = communities?.filter((c: any) =>
    c.members.some((m: string) => m.toLowerCase().includes(searchQuery.toLowerCase())) ||
    c.id.toString().includes(searchQuery)
  );

  const handleRunLouvain = async () => {
    try { await graphService.runLouvain(); refetch(); }
    catch (err) { console.error('Louvain Error:', err); }
  };

  const handleFindPath = async () => {
    if (!pathStart.trim() || !pathEnd.trim()) return;
    setPathLoading(true);
    setPathResult(null);
    try {
      const result = await graphService.getShortestPath(pathStart.trim(), pathEnd.trim());
      setPathResult(result);
    } catch {
      setPathResult({ status: 'error', message: 'Backend error — check entity names.' });
    } finally {
      setPathLoading(false);
    }
  };

  const centralityEntries = Object.entries(graphMetrics?.global_centrality ?? {})
    .sort(([, a], [, b]) => (b as number) - (a as number));
  const maxDegree = (centralityEntries[0]?.[1] as number) ?? 1;

  const modularity = analytics?.modularity;
  const modularityLabel =
    modularity == null ? '—'
    : modularity >= 0.5 ? 'Excellent'
    : modularity >= 0.3 ? 'Good'
    : 'Weak';
  const modularityColor =
    modularity == null ? 'text-gray-400'
    : modularity >= 0.5 ? 'text-green-600'
    : modularity >= 0.3 ? 'text-yellow-600'
    : 'text-red-500';

  return (
    <div className="space-y-6 max-w-7xl mx-auto pb-12">

      {/* ── Header ── */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 dark:text-white flex items-center gap-2">
            <Layers className="text-purple-600" size={24} />
            Page 2 — Graph RAG
          </h1>
          <p className="text-gray-500 dark:text-gray-400">
            Neo4j Knowledge Graph · Louvain Communities · Centrality · Semantic Paths
          </p>
        </div>
        <button
          onClick={handleRunLouvain}
          disabled={isFetching}
          className="flex items-center gap-2 px-4 py-2 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg text-sm font-medium hover:bg-gray-50 transition-colors disabled:opacity-50"
        >
          <RefreshCcw size={16} className={isFetching ? 'animate-spin' : ''} />
          {isFetching ? 'Running…' : 'Re-run Louvain'}
        </button>
      </div>

      {/* ── Stats Bar ── */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        {[
          { label: 'Communities', value: communities?.length ?? 0,              icon: <Layers size={20} />,   color: 'purple' },
          { label: 'Entities',    value: graphMetrics?.total_nodes ?? 0,        icon: <Users size={20} />,    color: 'blue'   },
          { label: 'Relations',   value: graphMetrics?.total_edges ?? 0,        icon: <Share2 size={20} />,   color: 'green'  },
          { label: 'Density',     value: graphMetrics?.density?.toFixed(4) ?? '—', icon: <Database size={20} />, color: 'yellow' },
        ].map(({ label, value, icon, color }) => (
          <div key={label} className="bg-white dark:bg-gray-900 p-4 rounded-xl border border-gray-200 dark:border-gray-800 flex items-center gap-4">
            <div className={`p-3 bg-${color}-50 dark:bg-${color}-900/20 text-${color}-600 rounded-lg`}>{icon}</div>
            <div>
              <div className="text-[10px] uppercase font-bold text-gray-400 tracking-wider">{label}</div>
              <div className="text-xl font-bold text-gray-900 dark:text-white">{value}</div>
            </div>
          </div>
        ))}
      </div>

      {/* ── Modularity ── */}
      <div className="bg-white dark:bg-gray-900 rounded-xl border border-gray-200 dark:border-gray-800 p-5 flex items-center gap-6">
        <div className="p-4 bg-green-50 dark:bg-green-900/20 rounded-xl">
          <Target className="text-green-600" size={28} />
        </div>
        <div className="flex-1">
          <div className="text-[10px] font-bold uppercase text-gray-400 tracking-wider mb-1">Louvain Modularity Score</div>
          <div className="flex items-baseline gap-3">
            <span className="text-4xl font-black text-gray-900 dark:text-white">
              {modularity != null ? modularity.toFixed(4) : '—'}
            </span>
            <span className={`text-sm font-bold ${modularityColor}`}>{modularityLabel}</span>
          </div>
          <p className="text-[11px] text-gray-400 mt-1">
            Measures how well the graph separates into distinct communities (0 = random · 1 = perfect separation).
            Score ≥ 0.3 indicates meaningful cluster structure.
          </p>
        </div>
        <div className="hidden md:block">
          <div className="relative w-28 h-28">
            <svg viewBox="0 0 36 36" className="w-full h-full -rotate-90">
              <circle cx="18" cy="18" r="15.9" fill="none" stroke="#e2e8f0" strokeWidth="3" />
              <circle
                cx="18" cy="18" r="15.9" fill="none"
                stroke={modularity != null && modularity >= 0.5 ? '#16a34a' : modularity != null && modularity >= 0.3 ? '#ca8a04' : '#dc2626'}
                strokeWidth="3"
                strokeDasharray={`${(modularity ?? 0) * 100} 100`}
                strokeLinecap="round"
              />
            </svg>
            <div className="absolute inset-0 flex items-center justify-center">
              <span className="text-sm font-black text-gray-700 dark:text-gray-300">
                {modularity != null ? `${Math.round(modularity * 100)}%` : '—'}
              </span>
            </div>
          </div>
        </div>
      </div>

      {/* ── Cypher Browser (replaces Louvain ForceGraph) ── */}
      <div className="bg-white dark:bg-gray-900 rounded-2xl border border-gray-200 dark:border-gray-800 shadow-sm overflow-hidden">
        <div className="px-6 py-4 border-b border-gray-100 dark:border-gray-800 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Terminal className="text-green-500" size={18} />
            <h2 className="font-bold text-gray-900 dark:text-white">Cypher Browser</h2>
          </div>
          <span className="text-[10px] text-gray-400">Run any Cypher query · Ctrl+Enter · graph results render automatically</span>
        </div>

        <div className="p-6 space-y-4">
          {/* Editor */}
          <div className="rounded-xl overflow-hidden border border-gray-200 dark:border-gray-700">
            <div className="flex items-center justify-between px-4 py-2 bg-gray-900 border-b border-gray-700">
              <span className="text-[10px] font-mono text-green-400 uppercase tracking-widest">cypher</span>
              <button
                onClick={handleRunCypher}
                disabled={cypherLoading || !cypherQuery.trim()}
                className="flex items-center gap-1.5 px-3 py-1 bg-green-600 hover:bg-green-500 disabled:opacity-50 text-white rounded text-xs font-bold transition-colors"
              >
                {cypherLoading
                  ? <div className="w-3 h-3 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                  : <Play size={11} />}
                Run
              </button>
            </div>
            <textarea
              value={cypherQuery}
              onChange={(e) => setCypherQuery(e.target.value)}
              onKeyDown={(e) => { if (e.ctrlKey && e.key === 'Enter') handleRunCypher(); }}
              spellCheck={false}
              rows={6}
              className="w-full px-4 py-3 bg-gray-950 text-green-300 font-mono text-sm resize-y focus:outline-none leading-relaxed"
            />
          </div>

          {/* Error */}
          {cypherError && (
            <div className="px-4 py-3 bg-red-50 dark:bg-red-900/10 border border-red-200 dark:border-red-800 rounded-xl text-xs font-mono text-red-600 dark:text-red-400 whitespace-pre-wrap">
              {cypherError}
            </div>
          )}

          {/* Results — always as graph */}
          {cypherResult && (
            <div className="space-y-2">
              <div className="flex items-center gap-2">
                <span className="text-[10px] font-bold uppercase text-gray-400 tracking-wider">Results</span>
                <span className="text-[10px] px-2 py-0.5 bg-green-100 dark:bg-green-900/40 text-green-700 dark:text-green-400 rounded-full font-bold">
                  {cypherResult.count} row{cypherResult.count !== 1 ? 's' : ''}
                </span>
                <span className="text-[10px] px-2 py-0.5 bg-blue-100 dark:bg-blue-900/40 text-blue-700 dark:text-blue-300 rounded-full font-bold flex items-center gap-1">
                  <Share2 size={9} /> {cypherResult.is_graph ? 'graph' : 'table → graph'}
                </span>
              </div>

              {cypherResult.count === 0 ? (
                <p className="text-xs text-gray-400 italic py-4">No results returned.</p>
              ) : cypherGraphData ? (
                <div
                  ref={containerRef}
                  className="w-full rounded-xl overflow-hidden border border-gray-200 dark:border-gray-700 bg-gray-950"
                  style={{ height: 520 }}
                >
                  <ForceGraph2D
                    key={runId}
                    ref={graphRef}
                    graphData={cypherGraphData}
                    width={graphWidth || undefined}
                    height={520}
                    nodeLabel={(n: any) => n.label ?? n.id}
                    nodeAutoColorBy="community"
                    nodeRelSize={6}
                    nodeVal={(n: any) => n.group === 'hub' ? 60 : 8}
                    linkColor={() => 'rgba(148,163,184,0.45)'}
                    linkWidth={1.2}
                    linkDirectionalArrowLength={4}
                    linkDirectionalArrowRelPos={1}
                    linkCurvature={0.15}
                    d3AlphaDecay={0.015}
                    d3VelocityDecay={0.35}
                    warmupTicks={300}
                    cooldownTicks={0}
                    onEngineStop={handleEngineStop}
                    nodeCanvasObjectMode={() => 'after'}
                    nodeCanvasObject={(node: any, ctx, globalScale) => {
                      const label = String(node.label ?? node.id ?? '');
                      const isHub = node.group === 'hub';
                      const fontSize = Math.max(isHub ? 9 : 7, (isHub ? 13 : 10) / globalScale);
                      ctx.font = `${isHub ? 'bold ' : ''}${fontSize}px sans-serif`;
                      ctx.textAlign = 'center';
                      ctx.textBaseline = 'top';
                      ctx.fillStyle = isHub ? 'rgba(255,255,255,0.95)' : 'rgba(200,200,200,0.8)';
                      ctx.fillText(label, node.x as number, (node.y as number) + (isHub ? 9 : 7));
                    }}
                  />
                </div>
              ) : null}
            </div>
          )}
        </div>
      </div>

      {/* ── Advanced Analytics ── */}
      <div className="bg-white dark:bg-gray-900 rounded-2xl border border-gray-200 dark:border-gray-800 shadow-sm overflow-hidden">
        <div className="px-6 py-4 border-b border-gray-100 dark:border-gray-800 flex items-center gap-2">
          <BarChart2 className="text-orange-500" size={18} />
          <h2 className="font-bold text-gray-900 dark:text-white">Advanced Analytics</h2>
          <span className="text-[10px] text-gray-400 ml-auto">Centrality · Density · Distribution</span>
        </div>
        <div className="p-6 grid grid-cols-1 lg:grid-cols-2 gap-6">

          <div>
            <div className="text-[10px] font-bold uppercase text-gray-400 tracking-wider mb-4 flex items-center gap-1.5">
              <Star size={11} className="text-yellow-500" /> Top Entities by Degree Centrality
            </div>
            {centralityEntries.length === 0 ? (
              <p className="text-xs text-gray-400 italic">No centrality data — run the graph pipeline first.</p>
            ) : (
              <div className="space-y-3">
                {centralityEntries.map(([name, degree], i) => {
                  const pct = Math.round(((degree as number) / maxDegree) * 100);
                  return (
                    <div key={name}>
                      <div className="flex items-center justify-between mb-1">
                        <div className="flex items-center gap-2">
                          <span className={`text-[10px] font-black w-4 text-center ${i === 0 ? 'text-yellow-500' : 'text-gray-400'}`}>
                            {i === 0 ? '★' : `#${i + 1}`}
                          </span>
                          <span className="text-xs font-semibold text-gray-700 dark:text-gray-300 truncate max-w-[160px]">{name}</span>
                        </div>
                        <span className="text-[10px] font-mono text-gray-500">{degree as number} links</span>
                      </div>
                      <div className="h-1.5 bg-gray-100 dark:bg-gray-800 rounded-full overflow-hidden">
                        <div className={`h-full rounded-full ${i === 0 ? 'bg-yellow-400' : 'bg-orange-400'}`} style={{ width: `${pct}%` }} />
                      </div>
                    </div>
                  );
                })}
              </div>
            )}
          </div>

          <div className="space-y-5">
            <div>
              <div className="text-[10px] font-bold uppercase text-gray-400 tracking-wider mb-3 flex items-center gap-1.5">
                <Network size={11} className="text-blue-500" /> Graph Density & Structure
              </div>
              <div className="grid grid-cols-2 gap-3">
                {[
                  { label: 'Density',    value: graphMetrics?.density?.toFixed(5) ?? '—',
                    note: graphMetrics?.density != null ? (graphMetrics.density < 0.01 ? 'Sparse graph' : graphMetrics.density < 0.1 ? 'Medium density' : 'Dense graph') : '', color: 'blue' },
                  { label: 'Avg Degree', value: graphMetrics?.total_nodes && graphMetrics?.total_edges ? ((graphMetrics.total_edges * 2) / graphMetrics.total_nodes).toFixed(1) : '—',
                    note: 'edges per node', color: 'purple' },
                  { label: 'Nodes',  value: graphMetrics?.total_nodes ?? '—', note: 'entities in KG',   color: 'green'  },
                  { label: 'Edges',  value: graphMetrics?.total_edges ?? '—', note: 'semantic relations', color: 'orange' },
                ].map(({ label, value, note, color }) => (
                  <div key={label} className={`p-3 rounded-lg bg-${color}-50 dark:bg-${color}-900/10 border border-${color}-100 dark:border-${color}-900/30`}>
                    <div className={`text-[9px] font-bold uppercase text-${color}-500 mb-1`}>{label}</div>
                    <div className="text-lg font-bold text-gray-900 dark:text-white">{value}</div>
                    <div className="text-[9px] text-gray-400">{note}</div>
                  </div>
                ))}
              </div>
            </div>

            <div>
              <div className="text-[10px] font-bold uppercase text-gray-400 tracking-wider mb-3 flex items-center gap-1.5">
                <Layers size={11} className="text-purple-500" /> Community Size Distribution
              </div>
              <div className="space-y-2">
                {communities?.slice(0, 5).map((comm: any) => {
                  const pct = Math.round((comm.size / (graphMetrics?.total_nodes || 1)) * 100);
                  return (
                    <div key={comm.id}>
                      <div className="flex justify-between text-[10px] mb-1">
                        <span className="text-gray-500 font-medium">Community #{comm.id}</span>
                        <span className="text-gray-700 dark:text-gray-300 font-bold">{comm.size} nodes · {pct}%</span>
                      </div>
                      <div className="h-1.5 bg-gray-100 dark:bg-gray-800 rounded-full overflow-hidden">
                        <div className="h-full rounded-full" style={{ width: `${pct}%`, background: COMMUNITY_COLORS[communities.indexOf(comm) % COMMUNITY_COLORS.length] }} />
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* ── Community Cards ── */}
      <div className="bg-white dark:bg-gray-900 rounded-2xl border border-gray-200 dark:border-gray-800 shadow-sm overflow-hidden">
        <div className="px-6 py-4 border-b border-gray-100 dark:border-gray-800 flex items-center gap-2">
          <Users className="text-blue-500" size={18} />
          <h2 className="font-bold text-gray-900 dark:text-white">Community Members</h2>
        </div>
        <div className="p-6 space-y-4">
          <div className="relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" size={14} />
            <input
              type="text"
              placeholder="Filter communities by member name or ID…"
              className="w-full pl-9 pr-4 py-2 bg-gray-50 dark:bg-gray-800 text-gray-900 dark:text-white border border-gray-200 dark:border-gray-700 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 text-sm placeholder-gray-400"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
            />
          </div>
          <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
            {isLoading
              ? [1, 2, 3].map(i => <div key={i} className="h-40 bg-gray-100 dark:bg-gray-800 animate-pulse rounded-xl" />)
              : filteredCommunities?.map((comm: any) => (
                <div key={comm.id} className="p-4 bg-gray-50 dark:bg-gray-800/60 rounded-xl border border-gray-100 dark:border-gray-700 hover:border-blue-300 dark:hover:border-blue-700 transition-all">
                  <div className="flex justify-between items-start mb-3">
                    <div>
                      <div className="w-3 h-3 rounded-full mb-1" style={{ background: COMMUNITY_COLORS[filteredCommunities.indexOf(comm) % COMMUNITY_COLORS.length] }} />
                      <h3 className="font-bold text-sm text-gray-900 dark:text-white">Community #{comm.id}</h3>
                    </div>
                    <span className="text-[10px] bg-blue-100 dark:bg-blue-900/40 text-blue-700 dark:text-blue-300 px-2 py-0.5 rounded-full font-bold">
                      {comm.size} nodes
                    </span>
                  </div>
                  <div className="flex flex-wrap gap-1">
                    {comm.members.slice(0, 6).map((m: string, idx: number) => (
                      <span key={idx} className="px-1.5 py-0.5 bg-white dark:bg-gray-900 border border-gray-100 dark:border-gray-700 rounded text-[10px] text-gray-600 dark:text-gray-400">{m}</span>
                    ))}
                    {comm.members.length > 6 && (
                      <span className="text-[10px] text-gray-400 italic">+{comm.members.length - 6} more</span>
                    )}
                  </div>
                </div>
              ))}
            {!isLoading && !filteredCommunities?.length && (
              <div className="col-span-full py-12 text-center text-gray-400 text-sm italic">
                No communities found. Try running Louvain analysis.
              </div>
            )}
          </div>
        </div>
      </div>

      {/* ── Semantic Paths & Recommendations ── */}
      <div className="bg-white dark:bg-gray-900 rounded-2xl border border-gray-200 dark:border-gray-800 shadow-sm overflow-hidden">
        <div className="px-6 py-4 border-b border-gray-100 dark:border-gray-800 flex items-center gap-2">
          <GitBranch className="text-green-500" size={18} />
          <h2 className="font-bold text-gray-900 dark:text-white">Semantic Paths</h2>
          <span className="text-[10px] text-gray-400 ml-auto">Find shortest path between any two entities</span>
        </div>
        <div className="p-6 space-y-5">
          <div className="flex flex-col sm:flex-row gap-3 items-end">
            <div className="flex-1">
              <label className="text-[10px] font-bold uppercase text-gray-400 block mb-1">Start Entity</label>
              <input type="text" value={pathStart} onChange={(e) => setPathStart(e.target.value)} placeholder="e.g. modèle de niche"
                className="w-full px-3 py-2 text-sm bg-gray-50 dark:bg-gray-800 text-gray-900 dark:text-white border border-gray-200 dark:border-gray-700 rounded-lg focus:outline-none focus:ring-2 focus:ring-green-500 placeholder-gray-400" />
            </div>
            <div className="hidden sm:flex items-center pb-2"><ArrowRight className="text-gray-300" size={18} /></div>
            <div className="flex-1">
              <label className="text-[10px] font-bold uppercase text-gray-400 block mb-1">End Entity</label>
              <input type="text" value={pathEnd} onChange={(e) => setPathEnd(e.target.value)} placeholder="e.g. biodiversité"
                className="w-full px-3 py-2 text-sm bg-gray-50 dark:bg-gray-800 text-gray-900 dark:text-white border border-gray-200 dark:border-gray-700 rounded-lg focus:outline-none focus:ring-2 focus:ring-green-500 placeholder-gray-400" />
            </div>
            <button onClick={handleFindPath} disabled={pathLoading || !pathStart.trim() || !pathEnd.trim()}
              className="px-5 py-2 bg-green-600 hover:bg-green-700 text-white rounded-lg text-sm font-bold disabled:opacity-50 flex items-center gap-2 transition-colors whitespace-nowrap">
              {pathLoading ? <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" /> : <Zap size={14} />}
              Find Path
            </button>
          </div>

          {pathResult && (
            pathResult.status === 'success' && pathResult.path?.length ? (
              <div className="p-4 bg-green-50 dark:bg-green-900/10 rounded-xl border border-green-200 dark:border-green-900/40">
                <div className="text-[10px] font-bold uppercase text-green-600 mb-3">Path found · {pathResult.path.length} hops</div>
                <div className="flex flex-wrap items-center gap-1">
                  {pathResult.path.map((node, i) => (
                    <React.Fragment key={i}>
                      <span className="px-2.5 py-1 bg-white dark:bg-gray-900 border border-green-300 dark:border-green-700 rounded-lg text-xs font-semibold text-gray-700 dark:text-gray-300">{node}</span>
                      {i < pathResult.path!.length - 1 && <ArrowRight size={12} className="text-green-400 mx-0.5" />}
                    </React.Fragment>
                  ))}
                </div>
              </div>
            ) : (
              <div className="p-4 bg-red-50 dark:bg-red-900/10 rounded-xl border border-red-200 dark:border-red-900/40 text-xs text-red-600 dark:text-red-400">
                {pathResult.message ?? 'No path found between these entities.'}
              </div>
            )
          )}

          <div>
            <div className="text-[10px] font-bold uppercase text-gray-400 tracking-wider mb-3 flex items-center gap-1.5">
              <Star size={11} className="text-yellow-500" /> Contextual Recommendations — Key Entities to Explore
            </div>
            {centralityEntries.length === 0 ? (
              <p className="text-xs text-gray-400 italic">No data yet.</p>
            ) : (
              <div className="flex flex-wrap gap-2">
                {centralityEntries.map(([name, degree]) => (
                  <button key={name} onClick={() => setPathStart(name)}
                    className="px-3 py-1.5 bg-gray-50 dark:bg-gray-800 hover:bg-yellow-50 dark:hover:bg-yellow-900/10 border border-gray-200 dark:border-gray-700 hover:border-yellow-300 dark:hover:border-yellow-700 rounded-lg text-xs font-medium text-gray-600 dark:text-gray-400 hover:text-yellow-700 dark:hover:text-yellow-400 transition-all flex items-center gap-1.5">
                    <Star size={10} className="text-yellow-400" />
                    {name}
                    <span className="text-[9px] text-gray-400 font-mono">{degree as number}</span>
                  </button>
                ))}
                <p className="w-full text-[10px] text-gray-400 mt-1 italic">Click any entity to set it as the path start point.</p>
              </div>
            )}
          </div>
        </div>
      </div>

    </div>
  );
};

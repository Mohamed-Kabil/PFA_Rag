import React from 'react';
import { Link } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { systemService, graphService } from '../../services/api-service';
import { KpiCard } from '../../components/dashboard/KpiCard';
import { GraphPreview } from '../../components/graph/GraphPreview';
import {
  Database,
  Share2,
  Users,
  Activity,
  FileText,
  Layers,
  GitBranch,
  Bot,
  MessageSquare,
  ArrowRight,
  Brain,
  Target,
  Clock,
} from 'lucide-react';

const MODULES = [
  {
    name: 'Vectorial RAG',
    subtitle: 'Page 1',
    description: 'Chunking · FAISS Embeddings · PCA 2D · Hybrid BM25 + Semantic',
    Icon: Database,
    href: '/vectorial',
    iconClass: 'text-blue-500',
    bgClass: 'bg-blue-50 dark:bg-blue-900/10',
    borderClass: 'border-blue-200 dark:border-blue-800',
    badgeClass: 'bg-blue-100 dark:bg-blue-900/40 text-blue-600 dark:text-blue-300',
    hoverClass: 'hover:border-blue-400 dark:hover:border-blue-500',
  },
  {
    name: 'Graph RAG',
    subtitle: 'Page 2',
    description: 'Neo4j Knowledge Graph · Louvain Communities · Modularity Analysis',
    Icon: GitBranch,
    href: '/communities',
    iconClass: 'text-green-500',
    bgClass: 'bg-green-50 dark:bg-green-900/10',
    borderClass: 'border-green-200 dark:border-green-800',
    badgeClass: 'bg-green-100 dark:bg-green-900/40 text-green-600 dark:text-green-300',
    hoverClass: 'hover:border-green-400 dark:hover:border-green-500',
  },
  {
    name: 'Agentic RAG',
    subtitle: 'Page 3',
    description: 'Q-Learning Policy · Decision Routing · Reward Monitor · Feedback Loop',
    Icon: Bot,
    href: '/agentic',
    iconClass: 'text-purple-500',
    bgClass: 'bg-purple-50 dark:bg-purple-900/10',
    borderClass: 'border-purple-200 dark:border-purple-800',
    badgeClass: 'bg-purple-100 dark:bg-purple-900/40 text-purple-600 dark:text-purple-300',
    hoverClass: 'hover:border-purple-400 dark:hover:border-purple-500',
  },
  {
    name: 'Query Interface',
    subtitle: 'Page 4',
    description: 'Semantic Search · Confidence Score · Routing Preview · History',
    Icon: MessageSquare,
    href: '/chat',
    iconClass: 'text-orange-500',
    bgClass: 'bg-orange-50 dark:bg-orange-900/10',
    borderClass: 'border-orange-200 dark:border-orange-800',
    badgeClass: 'bg-orange-100 dark:bg-orange-900/40 text-orange-600 dark:text-orange-300',
    hoverClass: 'hover:border-orange-400 dark:hover:border-orange-500',
  },
];

const ACTION_COLOR: Record<string, string> = {
  Vector: 'blue',
  Graph: 'green',
  Hybrid: 'purple',
};

export const Dashboard: React.FC = () => {
  const { data: graphMetrics, isLoading: loadingGraph } = useQuery({
    queryKey: ['graph-metrics'],
    queryFn: () => graphService.getGraphMetrics(),
  });

  const { data: chunkingStats, isLoading: loadingChunks } = useQuery({
    queryKey: ['chunking-stats'],
    queryFn: systemService.getChunkingStats,
  });

  const { data: communities, isLoading: loadingCommunities } = useQuery({
    queryKey: ['communities'],
    queryFn: graphService.getCommunities,
  });

  const { data: systemHealth, isLoading: loadingHealth } = useQuery({
    queryKey: ['system-health'],
    queryFn: systemService.getHealth,
  });

  const { data: agentState } = useQuery({
    queryKey: ['agent-state'],
    queryFn: systemService.getAgentState,
    refetchInterval: 15_000,
  });

  const { data: analytics } = useQuery({
    queryKey: ['analytics'],
    queryFn: systemService.getAnalytics,
  });

  const lastDecision = agentState?.last_decisions?.at(-1);
  const lastQValues = lastDecision?.q_values ?? {};

  const modeStats = React.useMemo(() => {
    const decisions = agentState?.last_decisions ?? [];
    const total = decisions.length || 1;
    return ['Vector', 'Graph', 'Hybrid'].map((mode) => ({
      mode,
      count: decisions.filter((d) => d.action_taken === mode).length,
      pct: Math.round(
        (decisions.filter((d) => d.action_taken === mode).length / total) * 100
      ),
    }));
  }, [agentState]);

  return (
    <div className="space-y-6 max-w-[1600px] mx-auto">
      {/* ── Header ── */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 dark:text-white flex items-center gap-2">
            Knowledge System Dashboard
            <span className="text-xs bg-blue-500 text-white px-2 py-1 rounded ml-1">v2.0</span>
          </h1>
          <p className="text-gray-500 dark:text-gray-400 mt-0.5">
            Agentic Vectorial Graph RAG — real-time system overview
          </p>
        </div>
        <div className="flex items-center gap-2 px-3 py-1.5 bg-green-50 dark:bg-green-900/20 text-green-700 dark:text-green-400 rounded-full text-sm font-medium border border-green-100 dark:border-green-800">
          <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse" />
          System Live
        </div>
      </div>

      {/* ── Module Navigation Cards ── */}
      <div className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-4 gap-4">
        {MODULES.map((m) => (
          <Link
            key={m.href}
            to={m.href}
            className={`group p-5 rounded-xl border-2 ${m.borderClass} ${m.bgClass} ${m.hoverClass} transition-all flex flex-col gap-3`}
          >
            <div className="flex items-start justify-between">
              <m.Icon className={m.iconClass} size={22} />
              <span className={`text-[10px] font-black uppercase tracking-wider px-2 py-0.5 rounded-full ${m.badgeClass}`}>
                {m.subtitle}
              </span>
            </div>
            <div>
              <div className="font-bold text-gray-900 dark:text-white text-sm">{m.name}</div>
              <p className="text-[11px] text-gray-500 dark:text-gray-400 mt-0.5 leading-relaxed">{m.description}</p>
            </div>
            <div className="flex items-center gap-1 text-[11px] font-semibold text-gray-400 group-hover:text-gray-700 dark:group-hover:text-gray-200 transition-colors mt-auto">
              Open module <ArrowRight size={11} className="group-hover:translate-x-0.5 transition-transform" />
            </div>
          </Link>
        ))}
      </div>

      {/* ── KPI Grid ── */}
      <div className="grid grid-cols-2 sm:grid-cols-3 xl:grid-cols-6 gap-4">
        <KpiCard
          title="Entities"
          value={graphMetrics?.total_nodes ?? 0}
          icon={<Users size={18} />}
          loading={loadingGraph}
        />
        <KpiCard
          title="Relations"
          value={graphMetrics?.total_edges ?? 0}
          icon={<Share2 size={18} />}
          loading={loadingGraph}
        />
        <KpiCard
          title="Communities"
          value={communities?.length ?? 0}
          icon={<Layers size={18} />}
          loading={loadingCommunities}
        />
        <KpiCard
          title="Chunks"
          value={chunkingStats?.total_chunks ?? 0}
          icon={<FileText size={18} />}
          loading={loadingChunks}
        />
        <KpiCard
          title="Modularity"
          value={analytics?.modularity != null ? analytics.modularity.toFixed(3) : '—'}
          icon={<Target size={18} />}
          description="Louvain score"
        />
        <KpiCard
          title="Status"
          value={systemHealth?.status ?? 'offline'}
          icon={<Activity size={18} />}
          loading={loadingHealth}
        />
      </div>

      {/* ── Main 2-col grid ── */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">

        {/* Left — Graph preview + Agent intelligence */}
        <div className="lg:col-span-2 space-y-6">

          {/* Graph Preview */}
          <div className="bg-white dark:bg-gray-900 p-6 rounded-xl shadow-sm border border-gray-200 dark:border-gray-800">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-base font-bold flex items-center gap-2">
                <Database className="text-blue-500" size={18} />
                Knowledge Graph Preview
              </h2>
              <span className="text-xs text-gray-400">Interactive · drag to explore</span>
            </div>
            <div className="h-[420px] bg-gray-50 dark:bg-gray-950 rounded-lg overflow-hidden border border-gray-100 dark:border-gray-800">
              <GraphPreview />
            </div>
          </div>

          {/* Agent Intelligence Panel */}
          <div className="bg-white dark:bg-gray-900 p-6 rounded-xl shadow-sm border border-gray-200 dark:border-gray-800">
            <div className="flex items-center justify-between mb-5">
              <h2 className="text-base font-bold flex items-center gap-2">
                <Brain className="text-purple-500" size={18} />
                Agent Intelligence
              </h2>
              <div className="flex items-center gap-4 text-[11px] font-mono">
                <span className="text-gray-400">
                  ε = <span className="font-bold text-purple-600 dark:text-purple-400">{agentState?.epsilon?.toFixed(2) ?? '—'}</span>
                </span>
                <span className="text-gray-400">
                  Q-states: <span className="font-bold text-blue-600 dark:text-blue-400">{agentState?.known_states ?? 0}</span>
                </span>
                <span className="text-gray-400">
                  α = <span className="font-bold text-gray-600 dark:text-gray-300">{agentState?.alpha?.toFixed(2) ?? '—'}</span>
                </span>
              </div>
            </div>

            {/* Routing mode distribution */}
            <div className="grid grid-cols-3 gap-3 mb-5">
              {modeStats.map(({ mode, count, pct }) => {
                const color = ACTION_COLOR[mode] ?? 'gray';
                return (
                  <div key={mode} className="p-3 bg-gray-50 dark:bg-gray-950 rounded-lg border border-gray-100 dark:border-gray-800">
                    <div className="text-[11px] text-gray-500 mb-1">{mode} Mode</div>
                    <div className={`text-xl font-bold text-${color}-600 dark:text-${color}-400`}>{pct}%</div>
                    <div className="w-full bg-gray-200 dark:bg-gray-800 h-1.5 mt-2 rounded-full overflow-hidden">
                      <div className={`bg-${color}-500 h-full rounded-full transition-all`} style={{ width: `${pct}%` }} />
                    </div>
                    <div className="text-[10px] text-gray-400 mt-1">{count} / {agentState?.last_decisions?.length ?? 0} queries</div>
                  </div>
                );
              })}
            </div>

            {/* Last decision Q-values + confidence */}
            {lastDecision ? (
              <div className="p-4 bg-purple-50 dark:bg-purple-900/10 rounded-xl border border-purple-100 dark:border-purple-900/30 space-y-3">
                <div className="flex items-center justify-between">
                  <span className="text-[10px] font-bold uppercase tracking-wider text-purple-500">Last Decision — Q-Values</span>
                  <div className="flex items-center gap-3 text-[10px] font-mono">
                    <span className="text-gray-500">
                      Confidence: <span className="font-bold text-purple-600">{((lastDecision.confidence_score ?? 0) * 100).toFixed(0)}%</span>
                    </span>
                    <span className="text-gray-500">
                      Reward: <span className={`font-bold ${(lastDecision.reward ?? 0) >= 0 ? 'text-green-600' : 'text-red-500'}`}>
                        {lastDecision.reward >= 0 ? '+' : ''}{lastDecision.reward?.toFixed(1)}
                      </span>
                    </span>
                    <span className={`px-2 py-0.5 rounded-full text-[9px] font-bold bg-${ACTION_COLOR[lastDecision.action_taken] ?? 'gray'}-100 dark:bg-${ACTION_COLOR[lastDecision.action_taken] ?? 'gray'}-900/40 text-${ACTION_COLOR[lastDecision.action_taken] ?? 'gray'}-700 dark:text-${ACTION_COLOR[lastDecision.action_taken] ?? 'gray'}-300`}>
                      {lastDecision.action_taken}
                    </span>
                  </div>
                </div>
                <div className="grid grid-cols-3 gap-2">
                  {['Vector', 'Graph', 'Hybrid'].map((a) => {
                    const qv = lastQValues[a] ?? 0;
                    const allQ = Object.values(lastQValues).map(Number);
                    const maxQv = Math.max(...allQ, 0.001);
                    const isSelected = lastDecision.action_taken === a;
                    const color = ACTION_COLOR[a] ?? 'gray';
                    return (
                      <div
                        key={a}
                        className={`text-center p-2.5 rounded-lg border transition-all ${
                          isSelected
                            ? `border-${color}-300 dark:border-${color}-700 bg-${color}-100 dark:bg-${color}-900/30`
                            : 'border-gray-100 dark:border-gray-800 bg-white dark:bg-gray-900'
                        }`}
                      >
                        <div className="text-[9px] text-gray-400 font-medium mb-0.5">{a}</div>
                        <div className={`text-sm font-bold font-mono ${isSelected ? `text-${color}-700 dark:text-${color}-300` : 'text-gray-500 dark:text-gray-400'}`}>
                          {qv.toFixed(3)}
                        </div>
                        <div className="w-full bg-gray-200 dark:bg-gray-700 h-1 mt-1 rounded-full overflow-hidden">
                          <div
                            className={`h-full rounded-full bg-${color}-400`}
                            style={{ width: `${maxQv > 0 ? Math.abs(qv / maxQv) * 100 : 0}%` }}
                          />
                        </div>
                        {isSelected && (
                          <div className={`text-[8px] font-bold mt-0.5 text-${color}-600 dark:text-${color}-400`}>selected</div>
                        )}
                      </div>
                    );
                  })}
                </div>
                <div className="text-[10px] text-gray-400 italic">
                  Query type: <span className="font-semibold text-gray-600 dark:text-gray-300">{lastDecision.query_type}</span>
                  {lastDecision.routing_reason && (
                    <> · {lastDecision.routing_reason}</>
                  )}
                </div>
              </div>
            ) : (
              <div className="p-4 bg-gray-50 dark:bg-gray-800/40 rounded-xl border border-gray-100 dark:border-gray-800 text-center">
                <p className="text-xs text-gray-400 italic">No queries processed yet.</p>
                <Link to="/chat" className="text-xs font-bold text-purple-500 hover:underline mt-1 inline-block">
                  Run a query →
                </Link>
              </div>
            )}
          </div>
        </div>

        {/* Right — Communities + Recent Queries */}
        <div className="space-y-6">

          {/* Top Communities */}
          <div className="bg-white dark:bg-gray-900 p-6 rounded-xl shadow-sm border border-gray-200 dark:border-gray-800">
            <h2 className="text-base font-bold mb-4 flex items-center gap-2">
              <Layers className="text-purple-500" size={18} />
              Top Communities
            </h2>
            {loadingCommunities ? (
              <div className="space-y-2">
                {[1, 2, 3, 4].map((i) => (
                  <div key={i} className="h-10 bg-gray-100 dark:bg-gray-800 animate-pulse rounded-lg" />
                ))}
              </div>
            ) : communities?.length ? (
              <div className="space-y-2">
                {communities.slice(0, 6).map((comm) => (
                  <div
                    key={comm.id}
                    className="p-2.5 bg-gray-50 dark:bg-gray-950 rounded-lg border border-gray-100 dark:border-gray-800 hover:border-blue-200 dark:hover:border-blue-900 transition-colors"
                  >
                    <div className="flex justify-between items-center">
                      <span className="text-sm font-bold">Community #{comm.id}</span>
                      <span className="text-[10px] bg-blue-100 dark:bg-blue-900/40 text-blue-700 dark:text-blue-300 px-2 py-0.5 rounded-full font-medium">
                        {comm.size} nodes
                      </span>
                    </div>
                    <p className="text-[10px] text-gray-500 mt-0.5 line-clamp-1 italic">
                      {comm.members?.join(', ')}
                    </p>
                  </div>
                ))}
                {communities.length > 6 && (
                  <Link to="/communities" className="block text-center text-[11px] text-blue-500 hover:underline font-medium pt-1">
                    View all {communities.length} communities →
                  </Link>
                )}
              </div>
            ) : (
              <div className="text-center py-6">
                <p className="text-gray-400 text-sm italic mb-3">No communities detected.</p>
                <button
                  onClick={() => graphService.runLouvain()}
                  className="text-xs font-bold text-blue-600 hover:underline"
                >
                  Run Louvain Analysis
                </button>
              </div>
            )}
          </div>

          {/* Recent Queries */}
          <div className="bg-white dark:bg-gray-900 p-6 rounded-xl shadow-sm border border-gray-200 dark:border-gray-800">
            <h2 className="text-base font-bold mb-4 flex items-center gap-2">
              <Clock className="text-orange-500" size={18} />
              Recent Queries
              {agentState?.last_decisions?.length ? (
                <span className="ml-auto text-[10px] font-normal text-gray-400">
                  last {Math.min(agentState.last_decisions.length, 5)} of {agentState.last_decisions.length}
                </span>
              ) : null}
            </h2>
            {!agentState?.last_decisions?.length ? (
              <div className="text-center py-6">
                <p className="text-sm text-gray-400 italic">No queries yet.</p>
                <Link to="/chat" className="text-xs font-bold text-orange-500 hover:underline mt-2 inline-block">
                  Try the Query interface →
                </Link>
              </div>
            ) : (
              <div className="space-y-2">
                {[...agentState.last_decisions].reverse().slice(0, 5).map((d, i) => {
                  const color = ACTION_COLOR[d.action_taken] ?? 'gray';
                  const confPct = Math.round((d.confidence_score ?? 0) * 100);
                  return (
                    <div
                      key={i}
                      className="p-3 bg-gray-50 dark:bg-gray-950 rounded-lg border border-gray-100 dark:border-gray-800"
                    >
                      <div className="flex items-center justify-between mb-1.5">
                        <span className={`text-[10px] font-bold px-2 py-0.5 rounded-full bg-${color}-100 dark:bg-${color}-900/40 text-${color}-700 dark:text-${color}-300`}>
                          {d.action_taken}
                        </span>
                        <div className="flex items-center gap-2 text-[10px] text-gray-400 font-mono">
                          <span className="text-purple-600 font-bold">{confPct}%</span>
                          <span className={`font-bold ${(d.reward ?? 0) >= 0 ? 'text-green-600' : 'text-red-500'}`}>
                            {d.reward >= 0 ? '+' : ''}{d.reward?.toFixed(1)}r
                          </span>
                        </div>
                      </div>
                      <p className="text-[10px] text-gray-500 dark:text-gray-400 line-clamp-1">
                        {d.routing_reason || d.query_type || '—'}
                      </p>
                      <div className="mt-1.5 w-full bg-gray-200 dark:bg-gray-700 h-1 rounded-full overflow-hidden">
                        <div
                          className={`h-full bg-${color}-400 rounded-full`}
                          style={{ width: `${confPct}%` }}
                        />
                      </div>
                    </div>
                  );
                })}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

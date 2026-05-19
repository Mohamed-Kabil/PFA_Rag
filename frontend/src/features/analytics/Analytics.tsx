import React from 'react';
import { useQuery } from '@tanstack/react-query';
import { systemService } from '../../services/api-service';
import {
  AreaChart, Area, XAxis, YAxis, CartesianGrid,
  Tooltip, ResponsiveContainer, PieChart, Pie, Cell, ReferenceLine,
} from 'recharts';
import {
  Bot, Brain, GitBranch, Zap, Activity, Cpu,
  Database, ArrowRight, CheckCircle2, XCircle,
  RefreshCcw, Target, TrendingUp,
} from 'lucide-react';

const ACTION_COLOR: Record<string, string> = {
  Vector: '#3b82f6',
  Graph:  '#a855f7',
  Hybrid: '#10b981',
};

export const Analytics: React.FC = () => {
  const { data: agentState, refetch } = useQuery({
    queryKey: ['agent-state'],
    queryFn: systemService.getAgentState,
    refetchInterval: 15_000,
  });

  // ── Derived ──────────────────────────────────────────
  const lastDecision = agentState?.last_decisions?.at(-1);

  const rewardData = React.useMemo(() => {
    if (!agentState?.last_decisions?.length) return [];
    let cumulative = 0;
    return agentState.last_decisions.map((d, i) => {
      cumulative += d.reward;
      return {
        index: i + 1,
        reward: d.reward,
        cumulative,
        action: d.action_taken,
      };
    });
  }, [agentState]);

  const successRate = React.useMemo(() => {
    const d = agentState?.last_decisions ?? [];
    if (!d.length) return 0;
    return Math.round((d.filter(x => x.reward > 0).length / d.length) * 100);
  }, [agentState]);

  const routingData = React.useMemo(() => {
    if (!agentState?.last_decisions?.length) return [];
    const counts: Record<string, number> = {};
    agentState.last_decisions.forEach(d => {
      counts[d.action_taken] = (counts[d.action_taken] ?? 0) + 1;
    });
    return Object.entries(counts).map(([name, value]) => ({
      name, value, color: ACTION_COLOR[name] ?? '#64748b',
    }));
  }, [agentState]);

  const qTableRows = React.useMemo(() => {
    if (!agentState?.q_table) return [];
    return Object.entries(agentState.q_table).map(([state, vals]) => {
      const [qVec, qGra, qHyb] = vals as number[];
      const best = Math.max(qVec, qGra, qHyb);
      return { state, Vector: qVec, Graph: qGra, Hybrid: qHyb, best };
    });
  }, [agentState]);

  const allQValues = qTableRows.flatMap(r => [r.Vector, r.Graph, r.Hybrid]);
  const qMin = Math.min(...allQValues, 0);
  const qMax = Math.max(...allQValues, 0.001);

  const qHeatColor = (v: number) => {
    if (v === 0) return 'bg-gray-100 dark:bg-gray-800 text-gray-400';
    const t = (v - qMin) / (qMax - qMin);
    if (t > 0.66) return 'bg-green-100 dark:bg-green-900/40 text-green-700 dark:text-green-300';
    if (t > 0.33) return 'bg-blue-100 dark:bg-blue-900/40 text-blue-700 dark:text-blue-300';
    return 'bg-purple-100 dark:bg-purple-900/40 text-purple-700 dark:text-purple-300';
  };

  const graphDecisions = agentState?.last_decisions?.filter(d => d.action_taken === 'Graph') ?? [];
  const alpha = agentState?.alpha ?? 0.1;
  const gamma = agentState?.gamma ?? 0.9;

  return (
    <div className="space-y-6 max-w-7xl mx-auto pb-12">

      {/* ── Header ── */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 dark:text-white flex items-center gap-2">
            <Bot className="text-purple-600" size={24} />
            Page 3 — Agentic RAG
          </h1>
          <p className="text-gray-500 dark:text-gray-400">
            Q-Learning policy · Decision routing · Reward monitor · Feedback loop
          </p>
        </div>
        <button
          onClick={() => refetch()}
          className="flex items-center gap-2 px-4 py-2 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg text-sm font-medium hover:bg-gray-50 transition-colors"
        >
          <RefreshCcw size={14} /> Refresh
        </button>
      </div>

      {/* ── KPI row ── */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        {[
          { label: 'Known States',  value: agentState?.known_states ?? 0,          icon: <Database size={18} />, color: 'blue',   note: 'Q-table entries' },
          { label: 'Epsilon ε',     value: agentState?.epsilon?.toFixed(2) ?? '—', icon: <Zap size={18} />,      color: 'purple', note: 'exploration rate' },
          { label: 'Alpha α',       value: agentState?.alpha?.toFixed(2) ?? '—',   icon: <Cpu size={18} />,      color: 'green',  note: 'learning rate' },
          { label: 'Gamma γ',       value: agentState?.gamma?.toFixed(2) ?? '—',   icon: <Target size={18} />,   color: 'orange', note: 'discount factor' },
        ].map(({ label, value, icon, color, note }) => (
          <div key={label} className="bg-white dark:bg-gray-900 p-5 rounded-xl border border-gray-200 dark:border-gray-800">
            <div className={`inline-flex p-2 rounded-lg bg-${color}-50 dark:bg-${color}-900/20 text-${color}-600 mb-3`}>{icon}</div>
            <div className="text-[10px] uppercase font-bold text-gray-400 tracking-wider">{label}</div>
            <div className="text-2xl font-bold text-gray-900 dark:text-white">{value}</div>
            <div className="text-[10px] text-gray-400 mt-0.5">{note}</div>
          </div>
        ))}
      </div>

      {/* ── Policy Visualization + Routing ── */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">

        {/* Q-table Heatmap */}
        <div className="lg:col-span-2 bg-white dark:bg-gray-900 rounded-2xl border border-gray-200 dark:border-gray-800 overflow-hidden">
          <div className="px-6 py-4 border-b border-gray-100 dark:border-gray-800 flex items-center gap-2">
            <Brain className="text-purple-500" size={18} />
            <h2 className="font-bold text-gray-900 dark:text-white">Policy Visualization — Q-Table</h2>
            <span className="text-[10px] text-gray-400 ml-auto">state → action Q-values</span>
          </div>
          <div className="p-6">
            {qTableRows.length === 0 ? (
              <div className="py-12 text-center text-gray-400 text-sm italic">
                No states learned yet — run queries via the Query interface to populate the Q-table.
              </div>
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full text-xs">
                  <thead>
                    <tr>
                      <th className="text-left text-[10px] uppercase text-gray-400 font-bold pb-3 pr-4">State</th>
                      {['Vector', 'Graph', 'Hybrid'].map(a => (
                        <th key={a} className="text-center text-[10px] uppercase font-bold pb-3 px-3" style={{ color: ACTION_COLOR[a] }}>
                          {a}
                        </th>
                      ))}
                      <th className="text-center text-[10px] uppercase text-gray-400 font-bold pb-3 pl-3">Best</th>
                    </tr>
                  </thead>
                  <tbody className="space-y-1">
                    {qTableRows.map((row) => (
                      <tr key={row.state} className="border-t border-gray-50 dark:border-gray-800">
                        <td className="py-2 pr-4">
                          <span className="px-2 py-0.5 bg-gray-100 dark:bg-gray-800 rounded text-[10px] font-mono text-gray-600 dark:text-gray-400">
                            {row.state}
                          </span>
                        </td>
                        {(['Vector', 'Graph', 'Hybrid'] as const).map(a => {
                          const v = row[a];
                          const isBest = v === row.best && v !== 0;
                          return (
                            <td key={a} className="py-2 px-3 text-center">
                              <span className={`inline-block px-2 py-1 rounded-lg text-[11px] font-mono font-bold ${qHeatColor(v)} ${isBest ? 'ring-2 ring-offset-1 ring-green-400' : ''}`}>
                                {v.toFixed(3)}
                              </span>
                            </td>
                          );
                        })}
                        <td className="py-2 pl-3 text-center">
                          <span className="text-[10px] font-bold px-2 py-0.5 rounded-full" style={{ background: ACTION_COLOR[['Vector','Graph','Hybrid'].find(a => row[a as keyof typeof row] === row.best) ?? 'Vector'] + '22', color: ACTION_COLOR[['Vector','Graph','Hybrid'].find(a => row[a as keyof typeof row] === row.best) ?? 'Vector'] }}>
                            {['Vector','Graph','Hybrid'].find(a => row[a as keyof typeof row] === row.best) ?? '—'}
                          </span>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
                <p className="text-[10px] text-gray-400 mt-3 italic">
                  Highlighted cell = highest Q-value per state (policy's preferred action). Green ring = selected.
                </p>
              </div>
            )}
          </div>
        </div>

        {/* Routing Distribution */}
        <div className="bg-white dark:bg-gray-900 rounded-2xl border border-gray-200 dark:border-gray-800 overflow-hidden">
          <div className="px-6 py-4 border-b border-gray-100 dark:border-gray-800 flex items-center gap-2">
            <Activity className="text-blue-500" size={18} />
            <h2 className="font-bold text-gray-900 dark:text-white">Routing Distribution</h2>
          </div>
          <div className="p-6 flex flex-col items-center gap-4">
            {routingData.length === 0 ? (
              <div className="py-10 text-center text-gray-400 text-sm italic">No decision history.</div>
            ) : (
              <>
                <div className="h-44 w-full">
                  <ResponsiveContainer width="100%" height="100%">
                    <PieChart>
                      <Pie data={routingData} cx="50%" cy="50%" innerRadius={48} outerRadius={70} paddingAngle={4} dataKey="value">
                        {routingData.map((entry, i) => (
                          <Cell key={i} fill={entry.color} stroke="none" />
                        ))}
                      </Pie>
                      <Tooltip contentStyle={{ fontSize: '11px', borderRadius: '8px' }} />
                    </PieChart>
                  </ResponsiveContainer>
                </div>
                <div className="w-full space-y-2">
                  {routingData.map(item => (
                    <div key={item.name} className="flex items-center gap-2">
                      <div className="w-2.5 h-2.5 rounded-full shrink-0" style={{ background: item.color }} />
                      <span className="text-xs text-gray-600 dark:text-gray-400 flex-1">{item.name}</span>
                      <span className="text-xs font-bold text-gray-800 dark:text-gray-200">{item.value} calls</span>
                    </div>
                  ))}
                </div>
              </>
            )}
          </div>
        </div>
      </div>

      {/* ── Reward Monitor ── */}
      <div className="bg-white dark:bg-gray-900 rounded-2xl border border-gray-200 dark:border-gray-800 overflow-hidden">
        <div className="px-6 py-4 border-b border-gray-100 dark:border-gray-800 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <TrendingUp className="text-green-500" size={18} />
            <h2 className="font-bold text-gray-900 dark:text-white">Reward Monitor</h2>
          </div>
          <div className="flex items-center gap-4 text-[11px]">
            <span className="text-gray-400">
              Success rate: <span className="font-bold text-green-600">{successRate}%</span>
            </span>
            <span className="text-gray-400">
              Total queries: <span className="font-bold text-gray-700 dark:text-gray-300">{agentState?.last_decisions?.length ?? 0}</span>
            </span>
          </div>
        </div>
        <div className="p-6">
          {rewardData.length === 0 ? (
            <div className="h-48 flex items-center justify-center text-gray-400 text-sm italic">No reward data yet.</div>
          ) : (
            <>
              <div className="h-52">
                <ResponsiveContainer width="100%" height="100%">
                  <AreaChart data={rewardData} margin={{ top: 8, right: 16, bottom: 0, left: 0 }}>
                    <defs>
                      <linearGradient id="rewardGrad" x1="0" y1="0" x2="0" y2="1">
                        <stop offset="5%"  stopColor="#10b981" stopOpacity={0.25} />
                        <stop offset="95%" stopColor="#10b981" stopOpacity={0} />
                      </linearGradient>
                      <linearGradient id="cumGrad" x1="0" y1="0" x2="0" y2="1">
                        <stop offset="5%"  stopColor="#3b82f6" stopOpacity={0.15} />
                        <stop offset="95%" stopColor="#3b82f6" stopOpacity={0} />
                      </linearGradient>
                    </defs>
                    <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#e2e8f0" opacity={0.4} />
                    <XAxis dataKey="index" tick={{ fontSize: 10 }} tickLine={false} axisLine={false} label={{ value: 'Query #', position: 'insideBottomRight', offset: -5, fontSize: 10 }} />
                    <YAxis tick={{ fontSize: 10 }} tickLine={false} axisLine={false} />
                    <ReferenceLine y={0} stroke="#94a3b8" strokeDasharray="4 4" />
                    <Tooltip
                      content={({ payload, label }) => {
                        if (!payload?.length) return null;
                        const d = payload[0]?.payload;
                        return (
                          <div className="bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-700 rounded-lg p-2.5 shadow text-xs">
                            <p className="font-bold mb-1">Query #{label} — <span style={{ color: ACTION_COLOR[d?.action] }}>{d?.action}</span></p>
                            <p className={`font-bold ${d?.reward > 0 ? 'text-green-600' : 'text-red-500'}`}>
                              Reward: {d?.reward > 0 ? '+' : ''}{d?.reward}
                            </p>
                            <p className="text-blue-500">Cumulative: {d?.cumulative?.toFixed(1)}</p>
                          </div>
                        );
                      }}
                    />
                    <Area type="step" dataKey="reward"     stroke="#10b981" strokeWidth={2} fill="url(#rewardGrad)" name="Reward" />
                    <Area type="monotone" dataKey="cumulative" stroke="#3b82f6" strokeWidth={1.5} fill="url(#cumGrad)" strokeDasharray="5 3" name="Cumulative" />
                  </AreaChart>
                </ResponsiveContainer>
              </div>
              <div className="flex items-center gap-6 mt-2 text-[10px] text-gray-400">
                <span className="flex items-center gap-1.5"><span className="w-4 h-0.5 bg-green-500 inline-block" /> Step reward (+1 / -1)</span>
                <span className="flex items-center gap-1.5"><span className="w-4 h-0.5 bg-blue-400 inline-block border-dashed border-t border-blue-400" /> Cumulative reward</span>
                <span className="flex items-center gap-1.5"><span className="w-4 h-px bg-gray-400 inline-block" style={{ borderTop: '1px dashed' }} /> Zero baseline</span>
              </div>
            </>
          )}
        </div>
      </div>

      {/* ── Decision Path ── */}
      <div className="bg-white dark:bg-gray-900 rounded-2xl border border-gray-200 dark:border-gray-800 overflow-hidden">
        <div className="px-6 py-4 border-b border-gray-100 dark:border-gray-800 flex items-center gap-2">
          <GitBranch className="text-blue-500" size={18} />
          <h2 className="font-bold text-gray-900 dark:text-white">Decision Path</h2>
          <span className="text-[10px] text-gray-400 ml-auto">Last query routing trace</span>
        </div>
        <div className="p-6">
          {!lastDecision ? (
            <div className="py-10 text-center text-gray-400 text-sm italic">No queries processed yet.</div>
          ) : (
            <div className="space-y-4">
              {/* Step flow */}
              <div className="flex flex-wrap items-center gap-2">
                {lastDecision.decision_path.map((step, i) => (
                  <React.Fragment key={i}>
                    <div className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium border ${
                      i === 0 ? 'bg-blue-50 dark:bg-blue-900/20 border-blue-200 dark:border-blue-800 text-blue-700 dark:text-blue-300'
                      : i === lastDecision.decision_path.length - 1 ? 'bg-green-50 dark:bg-green-900/20 border-green-200 dark:border-green-800 text-green-700 dark:text-green-300'
                      : 'bg-gray-50 dark:bg-gray-800 border-gray-200 dark:border-gray-700 text-gray-600 dark:text-gray-400'
                    }`}>
                      <span className="text-[9px] font-black opacity-60">{i + 1}</span>
                      {step}
                    </div>
                    {i < lastDecision.decision_path.length - 1 && (
                      <ArrowRight size={12} className="text-gray-300 shrink-0" />
                    )}
                  </React.Fragment>
                ))}
              </div>

              {/* Decision metadata */}
              <div className="grid grid-cols-2 md:grid-cols-4 gap-3 mt-2">
                {[
                  { label: 'Query Type',    value: lastDecision.query_type,                         color: 'blue' },
                  { label: 'Action Taken',  value: lastDecision.action_taken,                       color: 'purple' },
                  { label: 'Confidence',    value: `${((lastDecision.confidence_score ?? 0) * 100).toFixed(0)}%`, color: 'green' },
                  { label: 'Reward',        value: lastDecision.reward >= 0 ? `+${lastDecision.reward}` : `${lastDecision.reward}`, color: lastDecision.reward >= 0 ? 'green' : 'red' },
                ].map(({ label, value, color }) => (
                  <div key={label} className={`p-3 rounded-lg bg-${color}-50 dark:bg-${color}-900/10 border border-${color}-100 dark:border-${color}-900/30`}>
                    <div className={`text-[9px] font-bold uppercase text-${color}-500 mb-0.5`}>{label}</div>
                    <div className="text-sm font-bold text-gray-800 dark:text-gray-200">{value}</div>
                  </div>
                ))}
              </div>

              {lastDecision.routing_reason && (
                <p className="text-[11px] text-gray-500 italic px-1">{lastDecision.routing_reason}</p>
              )}
            </div>
          )}
        </div>
      </div>

      {/* ── Graph Query Execution + Hybrid Feedback Loop ── */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">

        {/* Graph Query Execution */}
        <div className="bg-white dark:bg-gray-900 rounded-2xl border border-gray-200 dark:border-gray-800 overflow-hidden">
          <div className="px-6 py-4 border-b border-gray-100 dark:border-gray-800 flex items-center gap-2">
            <Database className="text-green-500" size={18} />
            <h2 className="font-bold text-gray-900 dark:text-white">Graph Query Execution</h2>
            <span className="text-[10px] text-gray-400 ml-auto">{graphDecisions.length} Graph calls</span>
          </div>
          <div className="p-6">
            {graphDecisions.length === 0 ? (
              <div className="py-10 text-center text-gray-400 text-sm italic">
                No Graph-mode queries yet. The agent routes to Graph RAG for systematic / relational queries.
              </div>
            ) : (
              <div className="space-y-3">
                {[...graphDecisions].reverse().slice(0, 4).map((d, i) => (
                  <div key={i} className="p-3 bg-green-50 dark:bg-green-900/10 rounded-xl border border-green-100 dark:border-green-900/30">
                    <div className="flex items-center justify-between mb-1.5">
                      <span className="text-[10px] font-bold text-green-600 dark:text-green-400 uppercase tracking-wider">
                        Graph RAG · {d.query_type}
                      </span>
                      <div className="flex items-center gap-1.5">
                        {d.reward >= 0
                          ? <CheckCircle2 size={12} className="text-green-500" />
                          : <XCircle size={12} className="text-red-400" />}
                        <span className="text-[10px] font-mono text-gray-400">{((d.confidence_score ?? 0) * 100).toFixed(0)}% conf</span>
                      </div>
                    </div>
                    <p className="text-[11px] text-gray-600 dark:text-gray-400">{d.routing_reason || 'Graph traversal executed'}</p>
                    {d.retrieval_summary && (
                      <p className="text-[10px] text-gray-500 italic mt-1 line-clamp-2">{JSON.stringify(d.retrieval_summary).slice(0, 120)}</p>
                    )}
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>

        {/* Hybrid Feedback Loop */}
        <div className="bg-white dark:bg-gray-900 rounded-2xl border border-gray-200 dark:border-gray-800 overflow-hidden">
          <div className="px-6 py-4 border-b border-gray-100 dark:border-gray-800 flex items-center gap-2">
            <RefreshCcw className="text-purple-500" size={18} />
            <h2 className="font-bold text-gray-900 dark:text-white">Hybrid Feedback Loop</h2>
            <span className="text-[10px] text-gray-400 ml-auto">Q-table update cycle</span>
          </div>
          <div className="p-6 space-y-5">

            {/* Bellman equation */}
            <div className="p-4 bg-purple-50 dark:bg-purple-900/10 rounded-xl border border-purple-100 dark:border-purple-900/30">
              <div className="text-[10px] font-bold uppercase text-purple-500 mb-2">Bellman Update Equation</div>
              <div className="font-mono text-xs text-gray-600 dark:text-gray-400 leading-loose">
                Q(s,a) ← <span className="text-purple-600">(1-α)</span>·Q(s,a) + <span className="text-blue-600">α</span>·(r + <span className="text-green-600">γ</span>·max Q(s′,a′))
              </div>
              <div className="font-mono text-[10px] text-gray-400 mt-1">
                with α={alpha.toFixed(2)} · γ={gamma.toFixed(2)}
              </div>
            </div>

            {/* Live values from last update */}
            {lastDecision?.q_update ? (
              <div className="space-y-3">
                <div className="text-[10px] font-bold uppercase text-gray-400 tracking-wider">Last Update — {lastDecision.action_taken} action</div>

                <div className="flex items-center gap-3">
                  {/* Q old */}
                  <div className="flex-1 p-3 bg-gray-50 dark:bg-gray-800 rounded-lg text-center border border-gray-200 dark:border-gray-700">
                    <div className="text-[9px] text-gray-400 mb-0.5">Q_old</div>
                    <div className="text-base font-bold font-mono text-gray-700 dark:text-gray-300">
                      {lastDecision.q_update?.old_value?.toFixed(4) ?? '—'}
                    </div>
                  </div>

                  <ArrowRight className="text-gray-300 shrink-0" size={16} />

                  {/* Reward */}
                  <div className={`flex-1 p-3 rounded-lg text-center border ${lastDecision.reward >= 0 ? 'bg-green-50 dark:bg-green-900/20 border-green-200 dark:border-green-800' : 'bg-red-50 dark:bg-red-900/20 border-red-200 dark:border-red-800'}`}>
                    <div className="text-[9px] text-gray-400 mb-0.5">reward r</div>
                    <div className={`text-base font-bold font-mono ${lastDecision.reward >= 0 ? 'text-green-600' : 'text-red-500'}`}>
                      {lastDecision.reward >= 0 ? '+' : ''}{lastDecision.reward}
                    </div>
                  </div>

                  <ArrowRight className="text-gray-300 shrink-0" size={16} />

                  {/* Q new */}
                  <div className="flex-1 p-3 bg-purple-50 dark:bg-purple-900/20 rounded-lg text-center border border-purple-200 dark:border-purple-800">
                    <div className="text-[9px] text-gray-400 mb-0.5">Q_new</div>
                    <div className="text-base font-bold font-mono text-purple-600 dark:text-purple-400">
                      {lastDecision.q_update?.new_value?.toFixed(4) ?? '—'}
                    </div>
                  </div>
                </div>

                {/* Delta */}
                {lastDecision.q_update?.old_value != null && lastDecision.q_update?.new_value != null && (
                  <div className="flex items-center justify-between px-3 py-2 bg-gray-50 dark:bg-gray-800 rounded-lg text-[11px]">
                    <span className="text-gray-500">Q-value delta</span>
                    <span className={`font-bold font-mono ${(lastDecision.q_update.new_value - lastDecision.q_update.old_value) >= 0 ? 'text-green-600' : 'text-red-500'}`}>
                      {((lastDecision.q_update.new_value - lastDecision.q_update.old_value) >= 0 ? '+' : '')}
                      {(lastDecision.q_update.new_value - lastDecision.q_update.old_value).toFixed(4)}
                    </span>
                  </div>
                )}

                <p className="text-[10px] text-gray-400 italic">
                  The agent received a {lastDecision.reward >= 0 ? 'positive' : 'negative'} reward and updated the Q-value for the <strong>{lastDecision.action_taken}</strong> action in state <code className="bg-gray-100 dark:bg-gray-800 px-1 rounded">{lastDecision.state}</code>.
                </p>
              </div>
            ) : (
              <div className="py-8 text-center text-gray-400 text-sm italic">No update recorded yet.</div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

import React from 'react';
import { Message } from '../../../stores/chat-store';
import {
  Database,
  FileText,
  Zap,
  ShieldCheck,
  GitBranch,
  Target
} from 'lucide-react';

interface RetrievalPanelProps {
  activeMessage: Message | null;
}

export const RetrievalPanel: React.FC<RetrievalPanelProps> = ({ activeMessage }) => {
  if (!activeMessage || activeMessage.role === 'user') {
    return (
      <div className="h-full flex flex-col items-center justify-center p-8 text-center text-gray-400">
        <div className="w-16 h-16 bg-gray-50 dark:bg-gray-800 rounded-full flex items-center justify-center mb-6">
          <Database size={32} />
        </div>
        <h3 className="text-sm font-bold text-gray-900 dark:text-white mb-2">Retrieval Transparency</h3>
        <p className="text-xs">Submit a query to see the underlying agentic decision process and real-time Q-Learning values.</p>
      </div>
    );
  }

  const { metadata } = activeMessage;

  return (
    <div className="h-full flex flex-col bg-white dark:bg-gray-900 overflow-hidden">
      <div className="p-6 border-b border-gray-100 dark:border-gray-800">
        <h3 className="text-lg font-bold text-gray-900 dark:text-white flex items-center gap-2">
          <Zap className="text-yellow-500" size={20} />
          Retrieval Intelligence
        </h3>
        <p className="text-[11px] text-gray-500 mt-1 uppercase tracking-wider font-bold">Real-time Execution Trace</p>
      </div>

      <div className="flex-1 overflow-y-auto p-6 space-y-8">
        {/* Routing Confidence */}
        <section>
          <div className="flex justify-between items-end mb-3">
            <h4 className="text-xs font-bold text-gray-400 uppercase tracking-widest">Confidence Score</h4>
            <span className="text-lg font-black text-blue-600">
              {((metadata?.confidence_score || 0) * 100).toFixed(1)}%
            </span>
          </div>
          <div className="w-full h-2 bg-gray-100 dark:bg-gray-800 rounded-full overflow-hidden">
            <div 
              className="h-full bg-blue-600 transition-all duration-1000" 
              style={{ width: `${(metadata?.confidence_score || 0) * 100}%` }}
            ></div>
          </div>
        </section>

        {/* Decision Path */}
        {metadata?.decision_path && (
          <section>
            <h4 className="text-xs font-bold text-gray-400 uppercase tracking-widest mb-4 flex items-center gap-2">
              <GitBranch size={14} />
              Decision Path
            </h4>
            <div className="space-y-3 relative before:absolute before:left-[7px] before:top-2 before:bottom-2 before:w-px before:bg-gray-100 dark:before:bg-gray-800">
              {metadata.decision_path.map((step: string, idx: number) => (
                <div key={idx} className="flex gap-3 pl-1 group">
                  <div className={`w-3.5 h-3.5 rounded-full border-2 border-white dark:border-gray-900 z-10 mt-1 shadow-sm ${
                    idx === (metadata.decision_path?.length ?? 0) - 1 ? 'bg-blue-600 animate-pulse' : 'bg-gray-200 dark:bg-gray-700'
                  }`}></div>
                  <span className="text-[11px] text-gray-600 dark:text-gray-400 leading-tight">
                    {step}
                  </span>
                </div>
              ))}
            </div>
          </section>
        )}

        {/* Q-Values Visualization */}
        {metadata?.q_values && (
          <section>
            <h4 className="text-xs font-bold text-gray-400 uppercase tracking-widest mb-4 flex items-center gap-2">
              <Target size={14} />
              Q-Table Values (State)
            </h4>
            <div className="space-y-4">
              {Object.entries(metadata.q_values).map(([name, val]: [string, any]) => (
                <div key={name} className="space-y-1.5">
                  <div className="flex justify-between text-[10px] font-bold">
                    <span className="text-gray-500">{name} Mode</span>
                    <span className="text-gray-900 dark:text-white">{(val as number).toFixed(3)}</span>
                  </div>
                  <div className="h-1.5 bg-gray-100 dark:bg-gray-800 rounded-full overflow-hidden">
                    <div 
                      className={`h-full ${metadata.action_taken === name ? 'bg-blue-500' : 'bg-gray-300 dark:bg-gray-600'}`}
                      style={{ width: `${Math.max(0, Math.min(100, (val as number + 1) * 50))}%` }}
                    ></div>
                  </div>
                </div>
              ))}
            </div>
          </section>
        )}

        {/* Source Chunks */}
        <section>
          <h4 className="text-xs font-bold text-gray-400 uppercase tracking-widest mb-4 flex items-center gap-2">
            <FileText size={14} />
            Retrieved Context ({metadata?.sources?.length || 0})
          </h4>
          <div className="space-y-3">
            {metadata?.sources?.map((source: any, idx: number) => (
              <div key={idx} className="p-4 bg-gray-50 dark:bg-gray-800 rounded-xl border border-gray-100 dark:border-gray-700 hover:border-blue-200 dark:hover:border-blue-900 transition-colors group">
                <div className="flex justify-between items-start mb-2">
                  <span className="text-[10px] font-bold px-2 py-0.5 bg-white dark:bg-gray-900 rounded border border-gray-200 dark:border-gray-700">
                    Source #{idx + 1}
                  </span>
                  {source.score && (
                    <span className="text-[10px] font-black text-blue-500 italic">
                      Score: {source.score.toFixed(4)}
                    </span>
                  )}
                </div>
                <p className="text-xs text-gray-600 dark:text-gray-400 line-clamp-3 leading-relaxed">
                  {source.text || source.content || (source.type === 'graph' ? 'Graph knowledge extracted from sub-graphs.' : 'Loading...')}
                </p>
              </div>
            ))}
          </div>
        </section>
      </div>

      <div className="p-6 border-t border-gray-100 dark:border-gray-800 bg-gray-50/50 dark:bg-gray-800/30">
        <div className="flex items-center gap-2 text-green-600 dark:text-green-400">
          <ShieldCheck size={16} />
          <span className="text-[10px] font-bold uppercase tracking-widest">Decision Trace Verified</span>
        </div>
      </div>
    </div>
  );
};


import React from 'react';
import { useSettingsStore } from '../../stores/settings-store';
import {
  Settings as SettingsIcon,
  Database,
  Share2,
  Monitor,
  Save,
  RotateCcw
} from 'lucide-react';

export const Settings: React.FC = () => {
  const { retrieval, graph, ui, setRetrieval, setGraph, setUi } = useSettingsStore();

  return (
    <div className="max-w-4xl mx-auto space-y-8 pb-20">
      <div>
        <h1 className="text-2xl font-bold text-gray-900 dark:text-white flex items-center gap-2">
          <SettingsIcon className="text-gray-500" size={24} />
          System Settings
        </h1>
        <p className="text-gray-500 dark:text-gray-400">Configure global parameters for retrieval, visualization, and UI behavior.</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
        {/* Navigation Sidebar */}
        <div className="space-y-1">
          {['Retrieval', 'Graph Physics', 'Interface', 'System'].map((item) => (
            <button key={item} className={`w-full text-left px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
              item === 'Retrieval' ? 'bg-blue-50 text-blue-600 dark:bg-blue-900/20 dark:text-blue-400' : 'text-gray-500 hover:bg-gray-100 dark:hover:bg-gray-800'
            }`}>
              {item}
            </button>
          ))}
        </div>

        {/* Content Area */}
        <div className="md:col-span-2 space-y-8">
          {/* Retrieval Settings */}
          <section className="bg-white dark:bg-gray-900 p-8 rounded-3xl border border-gray-200 dark:border-gray-800 shadow-sm space-y-6">
            <h3 className="text-lg font-bold flex items-center gap-2">
              <Database className="text-blue-500" size={20} />
              Retrieval Strategy
            </h3>
            
            <div className="space-y-6">
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-3">Top-K Results ({retrieval.topK})</label>
                <input 
                  type="range" min="1" max="20" value={retrieval.topK}
                  onChange={(e) => setRetrieval({ topK: parseInt(e.target.value) })}
                  className="w-full accent-blue-600 h-1.5 bg-gray-100 dark:bg-gray-800 rounded-lg appearance-none cursor-pointer"
                />
                <p className="mt-2 text-[11px] text-gray-400 italic">Number of source chunks to retrieve for each query.</p>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-3">Hybrid Alpha ({retrieval.hybridAlpha})</label>
                <input 
                  type="range" min="0" max="1" step="0.1" value={retrieval.hybridAlpha}
                  onChange={(e) => setRetrieval({ hybridAlpha: parseFloat(e.target.value) })}
                  className="w-full accent-blue-600 h-1.5 bg-gray-100 dark:bg-gray-800 rounded-lg appearance-none cursor-pointer"
                />
                <div className="flex justify-between text-[10px] text-gray-400 font-bold uppercase mt-2">
                  <span>Keyword (BM25)</span>
                  <span>Semantic (Embeddings)</span>
                </div>
              </div>

              <div className="flex items-center justify-between p-4 bg-gray-50 dark:bg-gray-800/50 rounded-xl border border-gray-100 dark:border-gray-800">
                <div>
                  <div className="text-sm font-bold">Cohere Reranker</div>
                  <div className="text-[11px] text-gray-400">Increase accuracy with cross-encoder re-scoring.</div>
                </div>
                <button 
                  onClick={() => setRetrieval({ useReranker: !retrieval.useReranker })}
                  className={`w-12 h-6 rounded-full transition-colors relative ${retrieval.useReranker ? 'bg-blue-600' : 'bg-gray-300 dark:bg-gray-700'}`}
                >
                  <div className={`absolute top-1 w-4 h-4 bg-white rounded-full transition-all ${retrieval.useReranker ? 'left-7' : 'left-1'}`}></div>
                </button>
              </div>
            </div>
          </section>

          {/* Graph Settings */}
          <section className="bg-white dark:bg-gray-900 p-8 rounded-3xl border border-gray-200 dark:border-gray-800 shadow-sm space-y-6">
            <h3 className="text-lg font-bold flex items-center gap-2">
              <Share2 className="text-purple-500" size={20} />
              Visualization Physics
            </h3>
            
            <div className="space-y-6">
              <div className="grid grid-cols-2 gap-6">
                <div>
                  <label className="block text-xs font-bold text-gray-400 uppercase mb-3">Node Size</label>
                  <input 
                    type="number" value={graph.nodeSize}
                    onChange={(e) => setGraph({ nodeSize: parseInt(e.target.value) })}
                    className="w-full px-4 py-2 bg-gray-50 dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg text-sm"
                  />
                </div>
                <div>
                  <label className="block text-xs font-bold text-gray-400 uppercase mb-3">Link Distance</label>
                  <input 
                    type="number" value={graph.linkDistance}
                    onChange={(e) => setGraph({ linkDistance: parseInt(e.target.value) })}
                    className="w-full px-4 py-2 bg-gray-50 dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg text-sm"
                  />
                </div>
              </div>

              <div className="flex items-center justify-between p-4 bg-gray-50 dark:bg-gray-800/50 rounded-xl border border-gray-100 dark:border-gray-800">
                <div>
                  <div className="text-sm font-bold">Physics Simulation</div>
                  <div className="text-[11px] text-gray-400">Enable real-time force calculations.</div>
                </div>
                <button 
                  onClick={() => setGraph({ enablePhysics: !graph.enablePhysics })}
                  className={`w-12 h-6 rounded-full transition-colors relative ${graph.enablePhysics ? 'bg-purple-600' : 'bg-gray-300 dark:bg-gray-700'}`}
                >
                  <div className={`absolute top-1 w-4 h-4 bg-white rounded-full transition-all ${graph.enablePhysics ? 'left-7' : 'left-1'}`}></div>
                </button>
              </div>
            </div>
          </section>

          {/* UI Preferences */}
          <section className="bg-white dark:bg-gray-900 p-8 rounded-3xl border border-gray-200 dark:border-gray-800 shadow-sm space-y-6">
            <h3 className="text-lg font-bold flex items-center gap-2">
              <Monitor className="text-green-500" size={20} />
              Interface Preferences
            </h3>
            
            <div className="space-y-4">
               <div className="flex items-center justify-between">
                 <span className="text-sm font-medium">Compact Sidebar</span>
                 <button 
                  onClick={() => setUi({ compactMode: !ui.compactMode })}
                  className={`w-12 h-6 rounded-full transition-colors relative ${ui.compactMode ? 'bg-green-600' : 'bg-gray-300 dark:bg-gray-700'}`}
                >
                  <div className={`absolute top-1 w-4 h-4 bg-white rounded-full transition-all ${ui.compactMode ? 'left-7' : 'left-1'}`}></div>
                </button>
               </div>
               <div className="flex items-center justify-between">
                 <span className="text-sm font-medium">Reduced Motion</span>
                 <button 
                  onClick={() => setUi({ showAnimations: !ui.showAnimations })}
                  className={`w-12 h-6 rounded-full transition-colors relative {!ui.showAnimations ? 'bg-green-600' : 'bg-gray-300 dark:bg-gray-700'}`}
                >
                  <div className={`absolute top-1 w-4 h-4 bg-white rounded-full transition-all {!ui.showAnimations ? 'left-7' : 'left-1'}`}></div>
                </button>
               </div>
            </div>
          </section>

          {/* Save / Reset */}
          <div className="flex gap-4">
            <button className="flex-1 py-4 bg-blue-600 text-white rounded-2xl font-bold flex items-center justify-center gap-2 shadow-lg shadow-blue-500/20 hover:bg-blue-700 transition-all active:scale-95">
              <Save size={18} />
              Save Configuration
            </button>
            <button className="px-6 py-4 bg-gray-100 dark:bg-gray-800 text-gray-500 rounded-2xl font-bold flex items-center justify-center gap-2 hover:bg-gray-200 transition-all">
              <RotateCcw size={18} />
              Reset Defaults
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

import React from 'react';
import { useGraphStore } from '../../../stores/graph-store';
import { Info, ExternalLink, Hash, Tag, Users } from 'lucide-react';

export const NodeInspector: React.FC = () => {
  const { selectedNode, setSelectedNode } = useGraphStore();

  if (!selectedNode) {
    return (
      <div className="h-full flex flex-col items-center justify-center text-gray-400 p-6 text-center">
        <div className="w-16 h-16 bg-gray-50 dark:bg-gray-800 rounded-full flex items-center justify-center mb-4">
          <Info size={32} />
        </div>
        <p className="text-sm">Select a node in the graph to inspect its properties and relationships.</p>
      </div>
    );
  }

  return (
    <div className="h-full flex flex-col bg-white dark:bg-gray-900 overflow-hidden">
      <div className="p-6 border-b border-gray-100 dark:border-gray-800 flex justify-between items-start">
        <div>
          <h3 className="text-lg font-bold text-gray-900 dark:text-white leading-tight">
            {selectedNode.label || selectedNode.id}
          </h3>
          <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-blue-100 dark:bg-blue-900/30 text-blue-700 dark:text-blue-400 mt-2">
            {selectedNode.type || 'Entity'}
          </span>
        </div>
        <button 
          onClick={() => setSelectedNode(null)}
          className="p-1 hover:bg-gray-100 dark:hover:bg-gray-800 rounded text-gray-400"
        >
          <ExternalLink size={18} />
        </button>
      </div>

      <div className="flex-1 overflow-y-auto p-6 space-y-6">
        <section>
          <h4 className="text-xs font-semibold text-gray-400 uppercase tracking-wider mb-3">Attributes</h4>
          <div className="space-y-3">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-gray-50 dark:bg-gray-800 rounded-lg text-gray-500">
                <Hash size={16} />
              </div>
              <div>
                <div className="text-[10px] text-gray-400 font-medium">ID</div>
                <div className="text-sm font-medium">{selectedNode.id}</div>
              </div>
            </div>
            <div className="flex items-center gap-3">
              <div className="p-2 bg-gray-50 dark:bg-gray-800 rounded-lg text-gray-500">
                <Users size={16} />
              </div>
              <div>
                <div className="text-[10px] text-gray-400 font-medium">Community</div>
                <div className="text-sm font-medium">#{selectedNode.community || 0}</div>
              </div>
            </div>
            <div className="flex items-center gap-3">
              <div className="p-2 bg-gray-50 dark:bg-gray-800 rounded-lg text-gray-500">
                <Tag size={16} />
              </div>
              <div>
                <div className="text-[10px] text-gray-400 font-medium">Degree</div>
                <div className="text-sm font-medium">{selectedNode.degree || 'N/A'}</div>
              </div>
            </div>
          </div>
        </section>

        <section>
          <h4 className="text-xs font-semibold text-gray-400 uppercase tracking-wider mb-3">Source Information</h4>
          <div className="p-4 bg-gray-50 dark:bg-gray-800 rounded-lg border border-gray-100 dark:border-gray-800">
            <p className="text-xs text-gray-600 dark:text-gray-400 leading-relaxed italic">
              "This entity was extracted from the primary corpus regarding ecosystem fragmentation and biodiversity impacts."
            </p>
          </div>
        </section>
      </div>

      <div className="p-6 border-t border-gray-100 dark:border-gray-800">
        <button className="w-full py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg text-sm font-medium transition-colors">
          Expand Neighbors
        </button>
      </div>
    </div>
  );
};

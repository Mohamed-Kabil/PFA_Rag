import React from 'react';
import { useGraphStore } from '../../../stores/graph-store';
import { X, Filter as FilterIcon, Check } from 'lucide-react';

interface FilterModalProps {
  isOpen: boolean;
  onClose: () => void;
  availableCommunities: number[];
}

export const FilterModal: React.FC<FilterModalProps> = ({ isOpen, onClose, availableCommunities }) => {
  const { filters, setFilters } = useGraphStore();

  if (!isOpen) return null;

  const toggleCommunity = (id: number) => {
    const newCommunities = filters.communities.includes(id)
      ? filters.communities.filter(c => c !== id)
      : [...filters.communities, id];
    setFilters({ communities: newCommunities });
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50 backdrop-blur-sm">
      <div className="bg-white dark:bg-gray-900 rounded-2xl shadow-xl border border-gray-200 dark:border-gray-800 w-full max-w-md overflow-hidden">
        <div className="p-6 border-b border-gray-100 dark:border-gray-800 flex justify-between items-center">
          <h3 className="text-lg font-bold text-gray-900 dark:text-white flex items-center gap-2">
            <FilterIcon size={20} className="text-blue-500" />
            Graph Filters
          </h3>
          <button onClick={onClose} className="p-2 hover:bg-gray-100 dark:hover:bg-gray-800 rounded-lg text-gray-500">
            <X size={20} />
          </button>
        </div>

        <div className="p-6 space-y-6">
          <section>
            <h4 className="text-sm font-bold text-gray-900 dark:text-white mb-4">Communities</h4>
            <div className="grid grid-cols-2 gap-2">
              {availableCommunities.map((id) => (
                <button
                  key={id}
                  onClick={() => toggleCommunity(id)}
                  className={`
                    flex items-center justify-between px-3 py-2 rounded-lg text-xs font-medium border transition-all
                    ${filters.communities.includes(id)
                      ? 'bg-blue-50 border-blue-200 text-blue-700 dark:bg-blue-900/30 dark:border-blue-800 dark:text-blue-300'
                      : 'bg-gray-50 border-gray-100 text-gray-500 hover:border-gray-300 dark:bg-gray-800 dark:border-gray-700 dark:hover:border-gray-600'}
                  `}
                >
                  <span>Community #{id}</span>
                  {filters.communities.includes(id) && <Check size={14} />}
                </button>
              ))}
            </div>
            {availableCommunities.length === 0 && (
              <p className="text-xs text-gray-400 italic">No communities detected. Run Louvain first.</p>
            )}
          </section>

          <section>
            <h4 className="text-sm font-bold text-gray-900 dark:text-white mb-4">Metrics</h4>
            <div className="space-y-4">
              <div>
                <label className="text-xs text-gray-500 mb-2 block">Minimum Node Degree ({filters.minDegree})</label>
                <input 
                  type="range" 
                  min="0" 
                  max="20" 
                  value={filters.minDegree}
                  onChange={(e) => setFilters({ minDegree: parseInt(e.target.value) })}
                  className="w-full h-1.5 bg-gray-200 dark:bg-gray-800 rounded-lg appearance-none cursor-pointer accent-blue-600"
                />
              </div>
            </div>
          </section>
        </div>

        <div className="p-6 bg-gray-50 dark:bg-gray-800/50 flex gap-3">
          <button 
            onClick={() => setFilters({ communities: [], minDegree: 0 })}
            className="flex-1 py-2 text-sm font-medium text-gray-600 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-800 rounded-lg transition-colors"
          >
            Reset All
          </button>
          <button 
            onClick={onClose}
            className="flex-1 py-2 text-sm font-medium bg-blue-600 text-white hover:bg-blue-700 rounded-lg shadow-sm transition-colors"
          >
            Apply Filters
          </button>
        </div>
      </div>
    </div>
  );
};

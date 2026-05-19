import React from 'react';
import { useQuery } from '@tanstack/react-query';
import { systemService } from '../../services/api-service';
import { 
  FileText, 
  Upload, 
  Search, 
  MoreVertical, 
  CheckCircle2, 
  Clock, 
  Activity,
  Database,
  Trash2,
  RefreshCw,
  Eye
} from 'lucide-react';

export const Documents: React.FC = () => {
  const { data: chunkingStats, isLoading } = useQuery({
    queryKey: ['chunking-stats'],
    queryFn: systemService.getChunkingStats
  });

  // Derived document list from chunking stats
  const documents = React.useMemo(() => {
    if (!chunkingStats) return [];
    
    // We represent the main corpus as the primary document
    return [
      {
        id: 1,
        name: chunkingStats.hierarchy?.document || 'corpus_clean.docx',
        size: '2.4 MB',
        chunks: chunkingStats.total_chunks || 0,
        entities: 'Auto-calculating...',
        status: 'processed',
        date: 'May 10, 2026',
        method: chunkingStats.current_method
      }
    ];
  }, [chunkingStats]);

  return (
    <div className="space-y-8 max-w-7xl mx-auto">
      {/* Header & Upload */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-6">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 dark:text-white flex items-center gap-2">
            <Database className="text-blue-600" size={24} />
            Document Management
          </h1>
          <p className="text-gray-500 dark:text-gray-400">Upload and monitor your knowledge base ingestion pipeline.</p>
        </div>
        <button className="flex items-center gap-2 px-6 py-3 bg-blue-600 hover:bg-blue-700 text-white rounded-xl font-bold shadow-lg shadow-blue-500/20 transition-all active:scale-95">
          <Upload size={18} />
          Upload New Document
        </button>
      </div>

      {/* Pipeline Status */}
      <div className="bg-white dark:bg-gray-900 p-8 rounded-3xl border border-gray-200 dark:border-gray-800 shadow-sm relative overflow-hidden">
        <div className="absolute top-0 right-0 p-4 opacity-5">
          <RefreshCw size={120} />
        </div>
        
        <h3 className="text-sm font-bold uppercase tracking-widest text-gray-400 mb-8 flex items-center gap-2">
          <Activity size={16} />
          Active Ingestion Pipeline
        </h3>

        <div className="relative flex flex-col md:flex-row justify-between items-start md:items-center gap-8 md:gap-4">
          {/* Step 1 */}
          <div className="flex flex-col items-center text-center z-10">
            <div className="w-12 h-12 rounded-full bg-blue-600 text-white flex items-center justify-center mb-3 shadow-lg shadow-blue-500/30">
              <CheckCircle2 size={24} />
            </div>
            <div className="text-sm font-bold">Extraction</div>
            <div className="text-[10px] text-gray-500">PDF/Docx Parsing</div>
          </div>
          
          <div className="hidden md:block flex-1 h-0.5 bg-blue-600/20 mx-4"></div>

          {/* Step 2 */}
          <div className="flex flex-col items-center text-center z-10">
            <div className="w-12 h-12 rounded-full bg-blue-600 text-white flex items-center justify-center mb-3 shadow-lg shadow-blue-500/30">
              <CheckCircle2 size={24} />
            </div>
            <div className="text-sm font-bold">Chunking</div>
            <div className="text-[10px] text-gray-500">{chunkingStats?.current_method || 'Hierarchical'}</div>
          </div>

          <div className="hidden md:block flex-1 h-0.5 bg-blue-600/20 mx-4"></div>

          {/* Step 3 */}
          <div className="flex flex-col items-center text-center z-10">
            <div className="w-12 h-12 rounded-full bg-blue-600 text-white flex items-center justify-center mb-3 shadow-lg shadow-blue-500/30">
              <CheckCircle2 size={24} />
            </div>
            <div className="text-sm font-bold">Embedding</div>
            <div className="text-[10px] text-gray-500">FAISS Vectorization</div>
          </div>

          <div className="hidden md:block flex-1 h-0.5 bg-blue-600/20 mx-4"></div>

          {/* Step 4 */}
          <div className="flex flex-col items-center text-center z-10">
            <div className="w-12 h-12 rounded-full bg-blue-600 text-white flex items-center justify-center mb-3 shadow-lg shadow-blue-500/30">
              <CheckCircle2 size={24} />
            </div>
            <div className="text-sm font-bold">Graph Extraction</div>
            <div className="text-[10px] text-gray-500">Neo4j Mapping</div>
          </div>
        </div>
      </div>

      {/* Documents Table */}
      <div className="bg-white dark:bg-gray-900 rounded-3xl border border-gray-200 dark:border-gray-800 shadow-sm overflow-hidden">
        <div className="px-6 py-4 border-b border-gray-100 dark:border-gray-800 flex justify-between items-center">
          <h3 className="font-bold text-gray-900 dark:text-white">Indexed Corpus</h3>
          <div className="relative w-64">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" size={16} />
            <input 
              type="text" 
              placeholder="Search files..."
              className="w-full pl-10 pr-4 py-2 bg-gray-50 dark:bg-gray-800 border border-gray-100 dark:border-gray-700 rounded-lg text-xs"
            />
          </div>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left">
            <thead>
              <tr className="bg-gray-50 dark:bg-gray-800/50 text-[10px] font-black text-gray-400 uppercase tracking-widest">
                <th className="px-6 py-4">Filename</th>
                <th className="px-6 py-4">Status</th>
                <th className="px-6 py-4 text-center">Chunks</th>
                <th className="px-6 py-4 text-center">Method</th>
                <th className="px-6 py-4">Indexed Date</th>
                <th className="px-6 py-4 text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-50 dark:divide-gray-800">
              {documents.map((doc) => (
                <tr key={doc.id} className="hover:bg-gray-50 dark:hover:bg-gray-800/50 transition-colors group">
                  <td className="px-6 py-4">
                    <div className="flex items-center gap-3">
                      <div className="p-2 bg-blue-50 dark:bg-blue-900/20 text-blue-600 rounded-lg">
                        <FileText size={18} />
                      </div>
                      <div>
                        <div className="text-sm font-bold text-gray-900 dark:text-white">{doc.name}</div>
                        <div className="text-[10px] text-gray-400">{doc.size}</div>
                      </div>
                    </div>
                  </td>
                  <td className="px-6 py-4">
                    <div className={`inline-flex items-center gap-1.5 px-2 py-0.5 rounded-full text-[10px] font-bold uppercase tracking-tight ${
                      doc.status === 'processed' 
                        ? 'bg-green-50 dark:bg-green-900/20 text-green-600' 
                        : 'bg-blue-50 dark:bg-blue-900/20 text-blue-600'
                    }`}>
                      {doc.status === 'processed' ? <CheckCircle2 size={12} /> : <Clock size={12} className="animate-spin" />}
                      {doc.status}
                    </div>
                  </td>
                  <td className="px-6 py-4 text-center text-sm font-medium text-gray-600 dark:text-gray-400">
                    {doc.chunks}
                  </td>
                  <td className="px-6 py-4 text-center text-[10px] font-bold uppercase text-gray-400">
                    {doc.method}
                  </td>
                  <td className="px-6 py-4 text-xs text-gray-500">
                    {doc.date}
                  </td>
                  <td className="px-6 py-4 text-right">
                    <div className="flex justify-end gap-2 opacity-0 group-hover:opacity-100 transition-opacity">
                      <button className="p-2 hover:bg-blue-50 dark:hover:bg-blue-900/20 text-blue-600 rounded-lg"><Eye size={16} /></button>
                      <button className="p-2 hover:bg-gray-100 dark:hover:bg-gray-800 text-gray-500 rounded-lg"><MoreVertical size={16} /></button>
                      <button className="p-2 hover:bg-red-50 dark:hover:bg-red-900/20 text-red-500 rounded-lg"><Trash2 size={16} /></button>
                    </div>
                  </td>
                </tr>
              ))}
              {isLoading && (
                <tr>
                  <td colSpan={6} className="px-6 py-10 text-center animate-pulse text-gray-400 italic text-sm">
                    Retrieving knowledge base structure...
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Hierarchical Chunk Preview */}
      {chunkingStats?.hierarchy && (
        <div className="bg-white dark:bg-gray-900 p-8 rounded-3xl border border-gray-200 dark:border-gray-800 shadow-sm">
          <h3 className="text-sm font-bold uppercase tracking-widest text-gray-400 mb-6">
            Hierarchical Preview (Doc {'->'} Chunks)
          </h3>
          <div className="space-y-4">
             <div className="p-4 bg-blue-50 dark:bg-blue-900/10 rounded-xl border border-blue-100 dark:border-blue-900/30">
                <div className="text-xs font-bold text-blue-600 dark:text-blue-400 mb-1">Root Document</div>
                <div className="text-sm font-bold">{chunkingStats.hierarchy.document}</div>
             </div>
             <div className="ml-8 space-y-3 relative before:absolute before:left-[-20px] before:top-0 before:bottom-0 before:w-px before:bg-gray-100 dark:before:bg-gray-800">
                {chunkingStats.hierarchy.sample_sub_chunks.map((text: string, i: number) => (
                  <div key={i} className="p-4 bg-gray-50 dark:bg-gray-800/50 rounded-xl border border-gray-100 dark:border-gray-700 relative before:absolute before:left-[-20px] before:top-1/2 before:w-[20px] before:h-px before:bg-gray-100 dark:before:bg-gray-800">
                    <div className="text-[10px] font-bold text-gray-400 mb-1">Chunk #{i+1}</div>
                    <p className="text-xs text-gray-600 dark:text-gray-400 italic leading-relaxed">
                      "{text}"
                    </p>
                  </div>
                ))}
             </div>
          </div>
        </div>
      )}
    </div>
  );
};

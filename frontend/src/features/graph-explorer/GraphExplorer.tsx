import React, { useEffect, useState, useRef, useCallback } from 'react';
import ForceGraph2D, { ForceGraphMethods } from 'react-force-graph-2d';
import { graphService } from '../../services/api-service';
import { useGraphStore } from '../../stores/graph-store';
import { NodeInspector } from './components/NodeInspector';
import { GraphSearch } from './components/GraphSearch';
import { FilterModal } from './components/FilterModal';
import { Filter, Maximize2, RefreshCw, ZoomIn, ZoomOut } from 'lucide-react';

export const GraphExplorer: React.FC = () => {
  const [data, setData] = useState({ nodes: [], links: [] });
  const [loading, setLoading] = useState(true);
  const [isFilterModalOpen, setIsFilterModalOpen] = useState(false);
  const graphRef = useRef<ForceGraphMethods>();
  const containerRef = useRef<HTMLDivElement>(null);
  const [dimensions, setDimensions] = useState({ width: 0, height: 0 });
  
  const { 
    setSelectedNode, 
    searchQuery,
    filters 
  } = useGraphStore();

  // Load data
  const fetchData = async () => {
    setLoading(true);
    try {
      const response = await graphService.getFullGraph();
      const links = response.edges.map((e: any) => ({
        source: e.source,
        target: e.target,
        label: e.label
      }));

      // Calculate degree for each node
      const nodeMap = new Map();
      response.nodes.forEach((n: any) => nodeMap.set(n.id, { ...n, degree: 0 }));
      links.forEach((l: any) => {
        if (nodeMap.has(l.source)) nodeMap.get(l.source).degree++;
        if (nodeMap.has(l.target)) nodeMap.get(l.target).degree++;
      });

      setData({ nodes: Array.from(nodeMap.values()) as any, links });
    } catch (error) {
      console.error("Error fetching graph data:", error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  // Handle Resize
  useEffect(() => {
    const updateDimensions = () => {
      if (containerRef.current) {
        setDimensions({
          width: containerRef.current.clientWidth,
          height: containerRef.current.clientHeight
        });
      }
    };
    updateDimensions();
    window.addEventListener('resize', updateDimensions);
    return () => window.removeEventListener('resize', updateDimensions);
  }, []);

  // Get unique communities for filter
  const availableCommunities = React.useMemo(() => {
    const comms = new Set(data.nodes.map((n: any) => n.community).filter(c => c !== undefined));
    return Array.from(comms).sort((a: any, b: any) => a - b) as number[];
  }, [data.nodes]);

  // Filter and Search logic
  const filteredData = React.useMemo(() => {
    let nodes = data.nodes;
    
    // Search filter
    if (searchQuery) {
      nodes = nodes.filter((n: any) => 
        n.label.toLowerCase().includes(searchQuery.toLowerCase()) ||
        n.id.toLowerCase().includes(searchQuery.toLowerCase())
      );
    }

    // Community filter
    if (filters.communities.length > 0) {
      nodes = nodes.filter((n: any) => filters.communities.includes(n.community));
    }

    // Degree filter
    if (filters.minDegree > 0) {
      nodes = nodes.filter((n: any) => n.degree >= filters.minDegree);
    }

    const nodeIds = new Set(nodes.map((n: any) => n.id));
    const links = data.links.filter((l: any) => 
      nodeIds.has(typeof l.source === 'object' ? l.source.id : l.source) && 
      nodeIds.has(typeof l.target === 'object' ? l.target.id : l.target)
    );

    return { nodes, links };
  }, [data, searchQuery, filters]);

  const handleNodeClick = useCallback((node: any) => {
    setSelectedNode(node);
    if (graphRef.current) {
      graphRef.current.centerAt(node.x, node.y, 1000);
      graphRef.current.zoom(2, 1000);
    }
  }, [setSelectedNode]);

  const handleZoomIn = () => graphRef.current?.zoom(graphRef.current.zoom() * 1.5, 400);
  const handleZoomOut = () => graphRef.current?.zoom(graphRef.current.zoom() / 1.5, 400);
  const handleResetView = () => graphRef.current?.zoomToFit(600, 80);

  return (
    <div className="h-[calc(100vh-120px)] flex gap-6">
      <FilterModal 
        isOpen={isFilterModalOpen} 
        onClose={() => setIsFilterModalOpen(false)} 
        availableCommunities={availableCommunities}
      />

      {/* Main Workspace */}
      <div className="flex-1 flex flex-col bg-white dark:bg-gray-900 rounded-2xl shadow-sm border border-gray-200 dark:border-gray-800 overflow-hidden relative">
        {/* Toolbar */}
        <div className="absolute top-4 left-4 right-4 z-10 flex justify-between items-center pointer-events-none">
          <div className="w-80 pointer-events-auto">
            <GraphSearch />
          </div>
          
          <div className="flex gap-2 pointer-events-auto">
            <div className="flex bg-white dark:bg-gray-800 rounded-lg shadow-sm border border-gray-200 dark:border-gray-700 p-1">
              <button onClick={handleZoomIn} className="p-2 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-md text-gray-500"><ZoomIn size={18} /></button>
              <button onClick={handleZoomOut} className="p-2 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-md text-gray-500"><ZoomOut size={18} /></button>
              <div className="w-px bg-gray-200 dark:bg-gray-700 mx-1 my-1"></div>
              <button onClick={handleResetView} className="p-2 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-md text-gray-500"><Maximize2 size={18} /></button>
            </div>
            
            <button 
              onClick={fetchData}
              className="p-3 bg-white dark:bg-gray-800 rounded-lg shadow-sm border border-gray-200 dark:border-gray-700 text-gray-500 hover:text-blue-500 transition-colors pointer-events-auto"
            >
              <RefreshCw size={18} className={loading ? 'animate-spin' : ''} />
            </button>
            
            <button 
              onClick={() => setIsFilterModalOpen(true)}
              className={`flex items-center gap-2 px-4 bg-white dark:bg-gray-800 rounded-lg shadow-sm border border-gray-200 dark:border-gray-700 text-gray-500 hover:text-blue-500 transition-colors pointer-events-auto ${filters.communities.length > 0 || filters.minDegree > 0 ? 'ring-2 ring-blue-500 border-transparent' : ''}`}
            >
              <Filter size={18} />
              <span className="text-sm font-medium">Filters</span>
            </button>
          </div>
        </div>

        {/* Legend */}
        <div className="absolute bottom-4 left-4 z-10 bg-white/80 dark:bg-gray-800/80 backdrop-blur p-3 rounded-lg border border-gray-200 dark:border-gray-700 shadow-sm">
          <h4 className="text-[10px] font-bold uppercase text-gray-400 mb-2 tracking-widest text-center">Visual Legend</h4>
          <div className="flex flex-col gap-2">
            <div className="flex items-center gap-2">
              <div className="w-2.5 h-2.5 rounded-full bg-blue-500"></div>
              <span className="text-[10px] font-medium text-gray-600 dark:text-gray-300">Semantic Nodes</span>
            </div>
            <div className="flex items-center gap-2">
              <div className="w-2.5 h-2.5 bg-gray-300 dark:bg-gray-600 rounded-sm"></div>
              <span className="text-[10px] font-medium text-gray-600 dark:text-gray-300">Relationships</span>
            </div>
          </div>
        </div>

        {/* Graph Canvas */}
        <div ref={containerRef} className="w-full h-full">
          {dimensions.width > 0 && (
            <ForceGraph2D
              ref={graphRef}
              graphData={filteredData}
              width={dimensions.width}
              height={dimensions.height}
              nodeLabel={(n: any) => `[${n.type}] ${n.label} (Degree: ${n.degree})`}
              nodeAutoColorBy="community"
              nodeRelSize={6}
              linkDirectionalArrowLength={4}
              linkDirectionalArrowRelPos={1}
              linkCurvature={0.25}
              warmupTicks={150}
              cooldownTicks={0}
              d3AlphaDecay={0.05}
              d3VelocityDecay={0.6}
              onEngineStop={() => setTimeout(() => graphRef.current?.zoomToFit(400, 60), 50)}
              linkColor={() => 'rgba(148,163,184,0.6)'}
              linkWidth={1.2}
              onNodeClick={handleNodeClick}
              nodeCanvasObjectMode={() => 'after'}
              nodeCanvasObject={(node: any, ctx, globalScale) => {
                const label = node.label as string;
                const fontSize = Math.max(8, 11 / globalScale);
                ctx.font = `${fontSize}px sans-serif`;
                ctx.textAlign = 'center';
                ctx.textBaseline = 'top';
                ctx.fillStyle = 'rgba(30,30,30,0.85)';
                ctx.fillText(label, node.x as number, (node.y as number) + 7);
              }}
            />
          )}
        </div>
      </div>

      {/* Side Inspector */}
      <div className="w-96 bg-white dark:bg-gray-900 rounded-2xl shadow-sm border border-gray-200 dark:border-gray-800 overflow-hidden">
        <NodeInspector />
      </div>
    </div>
  );
};


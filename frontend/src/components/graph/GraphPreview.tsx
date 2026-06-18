import React, { useEffect, useState, useRef } from 'react';
import ForceGraph2D from 'react-force-graph-2d';
import { apiClient } from '../../api/api-client';

interface GraphData {
  nodes: any[];
  links: any[];
}

export const GraphPreview: React.FC = () => {
  const [data, setData] = useState<GraphData>({ nodes: [], links: [] });
  const [loading, setLoading] = useState(true);
  const containerRef = useRef<HTMLDivElement>(null);
  const graphRef = useRef<any>(null);
  const [dimensions, setDimensions] = useState({ width: 0, height: 0 });

  // Measure container after it renders
  useEffect(() => {
    if (!containerRef.current) return;
    const ro = new ResizeObserver(([entry]) => {
      setDimensions({
        width: entry.contentRect.width,
        height: entry.contentRect.height,
      });
    });
    ro.observe(containerRef.current);
    return () => ro.disconnect();
  }, []);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const response = await apiClient.get('/graph_data', { timeout: 30000 });
        const links = response.data.edges.map((e: any) => ({
          source: e.source,
          target: e.target,
          label: e.label,
        }));
        setData({ nodes: response.data.nodes, links });
      } catch (error) {
        console.error('Error fetching graph data:', error);
      } finally {
        setLoading(false);
      }
    };
    fetchData();
  }, []);

  // Center after engine stops (warmupTicks already ran, so this fires once)
  const handleEngineStop = () => {
    setTimeout(() => graphRef.current?.zoomToFit(300, 50), 50);
  };

  return (
    <div ref={containerRef} className="relative w-full h-full min-h-[400px]">
      {loading && (
        <div className="absolute inset-0 flex items-center justify-center text-gray-400 text-sm">
          Loading Graph...
        </div>
      )}
      {!loading && data.nodes.length === 0 && (
        <div className="absolute inset-0 flex items-center justify-center text-gray-400 text-sm">
          No graph data available.
        </div>
      )}
      {!loading && dimensions.width > 0 && data.nodes.length > 0 && (
        <ForceGraph2D
          ref={graphRef}
          graphData={data}
          width={dimensions.width}
          height={dimensions.height > 0 ? dimensions.height : 420}
          nodeLabel="label"
          nodeAutoColorBy="community"
          nodeRelSize={5}
          linkColor={() => 'rgba(148,163,184,0.6)'}
          linkWidth={1.2}
          linkDirectionalArrowLength={4}
          linkDirectionalArrowRelPos={1}
          linkCurvature={0.2}
          warmupTicks={150}
          cooldownTicks={0}
          d3AlphaDecay={0.05}
          d3VelocityDecay={0.6}
          onEngineStop={handleEngineStop}
        />
      )}
    </div>
  );
};

'use client';

import { useEffect, useRef, useState } from 'react';
import * as d3 from 'd3';
import { X } from 'lucide-react';

interface Page {
  id: string;
  path: string;
  label: string;
  type: string;
  description: string;
  components: string[];
  dataSource: string[];
}

interface ApiRoute {
  id: string;
  path: string;
  method: string;
  description: string;
  usedBy: string[];
}

interface Connection {
  from: string;
  to: string;
  type: string;
  label: string;
}

interface Props {
  pages: Page[];
  apiRoutes: ApiRoute[];
  connections: Connection[];
}

interface Node {
  id: string;
  label: string;
  type: 'public' | 'admin' | 'auth' | 'api';
  path: string;
  description: string;
  x?: number;
  y?: number;
  fx?: number | null;
  fy?: number | null;
}

interface Link {
  source: string | Node;
  target: string | Node;
  type: string;
  label: string;
}

const TYPE_COLORS: Record<string, string> = {
  public: '#3b82f6',  // Blue
  admin: '#8b5cf6',   // Purple
  auth: '#6b7280',    // Gray
  api: '#10b981'      // Green
};

export default function ScreenMapGraph({ pages, apiRoutes, connections }: Props) {
  const svgRef = useRef<SVGSVGElement>(null);
  const [selectedNode, setSelectedNode] = useState<Node | null>(null);
  const [dimensions, setDimensions] = useState({ width: 900, height: 600 });

  useEffect(() => {
    const updateDimensions = () => {
      const container = svgRef.current?.parentElement;
      if (container) {
        setDimensions({
          width: container.clientWidth,
          height: Math.max(500, container.clientHeight)
        });
      }
    };
    updateDimensions();
    window.addEventListener('resize', updateDimensions);
    return () => window.removeEventListener('resize', updateDimensions);
  }, []);

  useEffect(() => {
    if (!svgRef.current || !pages.length) return;

    const svg = d3.select(svgRef.current);
    svg.selectAll('*').remove();

    const { width, height } = dimensions;

    // Create nodes from pages and API routes
    const nodes: Node[] = [
      ...pages.map(p => ({
        id: p.path,
        label: p.label,
        type: p.type as Node['type'],
        path: p.path,
        description: p.description
      })),
      ...apiRoutes.map(a => ({
        id: a.path,
        label: a.path.replace('/api/', ''),
        type: 'api' as const,
        path: a.path,
        description: a.description
      }))
    ];

    // Create links from connections
    const links: Link[] = connections.map(c => ({
      source: c.from,
      target: c.to,
      type: c.type,
      label: c.label
    }));

    // Create simulation
    const simulation = d3.forceSimulation(nodes as d3.SimulationNodeDatum[])
      .force('link', d3.forceLink(links)
        .id((d: any) => d.id)
        .distance(120)
      )
      .force('charge', d3.forceManyBody().strength(-400))
      .force('center', d3.forceCenter(width / 2, height / 2))
      .force('collision', d3.forceCollide().radius(50));

    // Create container group for zoom
    const g = svg.append('g');

    // Add zoom behavior
    const zoom = d3.zoom<SVGSVGElement, unknown>()
      .scaleExtent([0.3, 3])
      .on('zoom', (event) => {
        g.attr('transform', event.transform);
      });
    svg.call(zoom);

    // Draw links
    const link = g.append('g')
      .selectAll('line')
      .data(links)
      .join('line')
      .attr('stroke', d => d.type === 'data' ? '#10b981' : '#94a3b8')
      .attr('stroke-width', 2)
      .attr('stroke-dasharray', d => d.type === 'navigation' ? '5,5' : 'none')
      .attr('marker-end', 'url(#arrowhead)');

    // Arrow marker
    svg.append('defs').append('marker')
      .attr('id', 'arrowhead')
      .attr('viewBox', '-0 -5 10 10')
      .attr('refX', 25)
      .attr('refY', 0)
      .attr('orient', 'auto')
      .attr('markerWidth', 6)
      .attr('markerHeight', 6)
      .append('path')
      .attr('d', 'M 0,-5 L 10,0 L 0,5')
      .attr('fill', '#94a3b8');

    // Draw nodes
    const node = g.append('g')
      .selectAll('g')
      .data(nodes)
      .join('g')
      .attr('cursor', 'pointer');

    // Add drag behavior (with type assertion to avoid D3 type conflicts)
    const dragBehavior = d3.drag<SVGGElement, Node>()
      .on('start', (event, d) => {
        if (!event.active) simulation.alphaTarget(0.3).restart();
        d.fx = d.x;
        d.fy = d.y;
      })
      .on('drag', (event, d) => {
        d.fx = event.x;
        d.fy = event.y;
      })
      .on('end', (event, d) => {
        if (!event.active) simulation.alphaTarget(0);
        d.fx = null;
        d.fy = null;
      });

    node.call(dragBehavior as any);

    // Node circles
    node.append('circle')
      .attr('r', d => d.type === 'api' ? 15 : 20)
      .attr('fill', d => TYPE_COLORS[d.type] || '#6b7280')
      .attr('stroke', '#fff')
      .attr('stroke-width', 2)
      .on('click', (event, d) => {
        event.stopPropagation();
        setSelectedNode(d);
      })
      .on('mouseover', function() {
        d3.select(this).attr('stroke-width', 4);
      })
      .on('mouseout', function() {
        d3.select(this).attr('stroke-width', 2);
      });

    // Node labels
    node.append('text')
      .attr('dy', d => d.type === 'api' ? 30 : 35)
      .attr('text-anchor', 'middle')
      .attr('font-size', '11px')
      .attr('fill', '#374151')
      .text(d => d.label.length > 15 ? d.label.substring(0, 15) + '...' : d.label);

    // Update positions on tick
    simulation.on('tick', () => {
      link
        .attr('x1', (d: any) => d.source.x)
        .attr('y1', (d: any) => d.source.y)
        .attr('x2', (d: any) => d.target.x)
        .attr('y2', (d: any) => d.target.y);

      node.attr('transform', (d: any) => `translate(${d.x},${d.y})`);
    });

    // Click on background to deselect
    svg.on('click', () => setSelectedNode(null));

    return () => {
      simulation.stop();
    };
  }, [pages, apiRoutes, connections, dimensions]);

  return (
    <div className="relative">
      {/* Legend */}
      <div className="absolute top-4 left-4 bg-white/90 backdrop-blur p-3 rounded-lg shadow-sm border border-gray-200 z-10">
        <h4 className="text-xs font-semibold text-gray-700 mb-2">Leyenda</h4>
        <div className="space-y-1">
          {Object.entries(TYPE_COLORS).map(([type, color]) => (
            <div key={type} className="flex items-center gap-2 text-xs">
              <div className="w-3 h-3 rounded-full" style={{ backgroundColor: color }} />
              <span className="capitalize">{type === 'api' ? 'API Routes' : type}</span>
            </div>
          ))}
        </div>
        <div className="mt-2 pt-2 border-t border-gray-200 space-y-1 text-xs text-gray-600">
          <div className="flex items-center gap-2">
            <div className="w-6 border-t-2 border-dashed border-gray-400" />
            <span>Navegacion</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-6 border-t-2 border-green-500" />
            <span>Datos</span>
          </div>
        </div>
      </div>

      {/* Stats */}
      <div className="absolute top-4 right-4 bg-white/90 backdrop-blur p-3 rounded-lg shadow-sm border border-gray-200 z-10">
        <div className="text-xs space-y-1">
          <div><span className="font-semibold">{pages.length}</span> paginas</div>
          <div><span className="font-semibold">{apiRoutes.length}</span> API routes</div>
          <div><span className="font-semibold">{connections.length}</span> conexiones</div>
        </div>
      </div>

      {/* SVG Canvas */}
      <svg
        ref={svgRef}
        width={dimensions.width}
        height={dimensions.height}
        className="bg-gray-50 rounded-lg"
      />

      {/* Selected Node Detail */}
      {selectedNode && (
        <div className="absolute bottom-4 left-4 right-4 bg-white rounded-lg shadow-lg border border-gray-200 p-4 z-20">
          <div className="flex items-start justify-between">
            <div>
              <div className="flex items-center gap-2">
                <div
                  className="w-4 h-4 rounded-full"
                  style={{ backgroundColor: TYPE_COLORS[selectedNode.type] }}
                />
                <h3 className="font-semibold text-gray-900">{selectedNode.label}</h3>
                <span className="text-xs px-2 py-0.5 bg-gray-100 rounded-full text-gray-600">
                  {selectedNode.type}
                </span>
              </div>
              <p className="text-sm text-gray-500 mt-1">{selectedNode.path}</p>
              <p className="text-sm text-gray-600 mt-2">{selectedNode.description}</p>
            </div>
            <button
              onClick={() => setSelectedNode(null)}
              className="p-1 hover:bg-gray-100 rounded"
            >
              <X className="w-4 h-4" />
            </button>
          </div>
        </div>
      )}
    </div>
  );
}

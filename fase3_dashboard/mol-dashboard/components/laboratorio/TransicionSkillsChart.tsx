"use client";

import { useEffect, useRef, useState } from "react";
import * as d3 from "d3";
import { X } from "lucide-react";

export const MAJOR_GROUP_COLORS: Record<string, string> = {
  "1": "#ef4444", // Directores
  "2": "#3b82f6", // Profesionales
  "3": "#8b5cf6", // Tecnicos
  "4": "#6b7280", // Administrativos
  "5": "#f59e0b", // Servicios/ventas
  "7": "#10b981", // Oficiales/operarios
  "8": "#06b6d4", // Operadores
  "9": "#ec4899", // Elementales
};

const MAJOR_GROUP_LABELS: Record<string, string> = {
  "1": "Directores",
  "2": "Profesionales",
  "3": "Tecnicos",
  "4": "Administrativos",
  "5": "Servicios/ventas",
  "7": "Oficiales/operarios",
  "8": "Operadores",
  "9": "Elementales",
};

export interface TransicionNodo {
  isco_code: string;
  isco_label: string;
  total_ofertas: number;
  total_skills: number;
}

export interface TransicionEnlace {
  source_isco: string;
  target_isco: string;
  jaccard: number;
  shared_skills: number;
  union_skills: number;
  top_shared_labels: string | null;
}

interface SimNode extends d3.SimulationNodeDatum {
  id: string;
  label: string;
  total_ofertas: number;
  total_skills: number;
  majorGroup: string;
}

interface SimLink extends d3.SimulationLinkDatum<SimNode> {
  jaccard: number;
  shared_skills: number;
  top_shared_labels: string[];
}

interface TransicionSkillsChartProps {
  nodes: TransicionNodo[];
  links: TransicionEnlace[];
}

interface SelectedNode {
  label: string;
  isco_code: string;
  total_ofertas: number;
  total_skills: number;
  connections: { target: string; jaccard: number; shared: string[] }[];
}

export function TransicionSkillsChart({
  nodes,
  links,
}: TransicionSkillsChartProps) {
  const svgRef = useRef<SVGSVGElement>(null);
  const [selectedNode, setSelectedNode] = useState<SelectedNode | null>(null);
  const [dimensions, setDimensions] = useState({ width: 900, height: 600 });

  useEffect(() => {
    const updateDimensions = () => {
      const container = svgRef.current?.parentElement;
      if (container) {
        setDimensions({
          width: container.clientWidth,
          height: Math.max(500, 600),
        });
      }
    };
    updateDimensions();
    window.addEventListener("resize", updateDimensions);
    return () => window.removeEventListener("resize", updateDimensions);
  }, []);

  useEffect(() => {
    if (!svgRef.current || !nodes.length) return;

    const svg = d3.select(svgRef.current);
    svg.selectAll("*").remove();

    const { width, height } = dimensions;

    const maxOfertas = Math.max(...nodes.map((n) => n.total_ofertas), 1);

    const simNodes: SimNode[] = nodes.map((n) => ({
      id: n.isco_code,
      label: n.isco_label,
      total_ofertas: n.total_ofertas,
      total_skills: n.total_skills,
      majorGroup: n.isco_code.charAt(0),
    }));

    const nodeMap = new Map(simNodes.map((n) => [n.id, n]));

    const simLinks: SimLink[] = links
      .filter((l) => nodeMap.has(l.source_isco) && nodeMap.has(l.target_isco))
      .map((l) => {
        let parsed: string[] = [];
        if (l.top_shared_labels) {
          try {
            parsed = JSON.parse(l.top_shared_labels);
          } catch {
            parsed = [];
          }
        }
        return {
          source: l.source_isco,
          target: l.target_isco,
          jaccard: l.jaccard,
          shared_skills: l.shared_skills,
          top_shared_labels: parsed,
        };
      });

    const simulation = d3
      .forceSimulation(simNodes)
      .force(
        "link",
        d3
          .forceLink<SimNode, SimLink>(simLinks)
          .id((d) => d.id)
          .distance((d) => 150 - d.jaccard * 200)
      )
      .force("charge", d3.forceManyBody().strength(-300))
      .force("center", d3.forceCenter(width / 2, height / 2))
      .force("collision", d3.forceCollide().radius(40));

    const g = svg.append("g");

    const zoom = d3
      .zoom<SVGSVGElement, unknown>()
      .scaleExtent([0.3, 3])
      .on("zoom", (event) => {
        g.attr("transform", event.transform);
      });
    svg.call(zoom);

    // Links
    const link = g
      .append("g")
      .selectAll("line")
      .data(simLinks)
      .join("line")
      .attr("stroke", "#94a3b8")
      .attr("stroke-width", (d) => Math.max(1, d.jaccard * 8))
      .attr("stroke-opacity", (d) => 0.3 + d.jaccard * 0.5);

    // Nodes
    const node = g
      .append("g")
      .selectAll("g")
      .data(simNodes)
      .join("g")
      .attr("cursor", "pointer");

    const dragBehavior = d3
      .drag<SVGGElement, SimNode>()
      .on("start", (event, d) => {
        if (!event.active) simulation.alphaTarget(0.3).restart();
        d.fx = d.x;
        d.fy = d.y;
      })
      .on("drag", (event, d) => {
        d.fx = event.x;
        d.fy = event.y;
      })
      .on("end", (event, d) => {
        if (!event.active) simulation.alphaTarget(0);
        d.fx = null;
        d.fy = null;
      });

    node.call(dragBehavior as any);

    // Circles
    node
      .append("circle")
      .attr("r", (d) => 10 + (d.total_ofertas / maxOfertas) * 20)
      .attr(
        "fill",
        (d) => MAJOR_GROUP_COLORS[d.majorGroup] || "#6b7280"
      )
      .attr("stroke", "#fff")
      .attr("stroke-width", 2)
      .on("click", (event, d) => {
        event.stopPropagation();
        const conns = simLinks
          .filter(
            (l) =>
              (l.source as SimNode).id === d.id ||
              (l.target as SimNode).id === d.id
          )
          .map((l) => {
            const other =
              (l.source as SimNode).id === d.id
                ? (l.target as SimNode)
                : (l.source as SimNode);
            return {
              target: other.label,
              jaccard: l.jaccard,
              shared: l.top_shared_labels,
            };
          })
          .sort((a, b) => b.jaccard - a.jaccard);

        setSelectedNode({
          label: d.label,
          isco_code: d.id,
          total_ofertas: d.total_ofertas,
          total_skills: d.total_skills,
          connections: conns,
        });
      })
      .on("mouseover", function () {
        d3.select(this).attr("stroke-width", 4);
      })
      .on("mouseout", function () {
        d3.select(this).attr("stroke-width", 2);
      });

    // Labels
    node
      .append("text")
      .attr("dy", (d) => 15 + (d.total_ofertas / maxOfertas) * 20)
      .attr("text-anchor", "middle")
      .attr("font-size", "10px")
      .attr("fill", "#374151")
      .text((d) =>
        d.label.length > 18 ? d.label.substring(0, 17) + "..." : d.label
      );

    simulation.on("tick", () => {
      link
        .attr("x1", (d: any) => d.source.x)
        .attr("y1", (d: any) => d.source.y)
        .attr("x2", (d: any) => d.target.x)
        .attr("y2", (d: any) => d.target.y);

      node.attr("transform", (d: any) => `translate(${d.x},${d.y})`);
    });

    svg.on("click", () => setSelectedNode(null));

    return () => {
      simulation.stop();
    };
  }, [nodes, links, dimensions]);

  return (
    <div className="relative" data-testid="transicion-chart-container">
      {/* Legend */}
      <div className="absolute top-4 left-4 bg-white/90 backdrop-blur p-3 rounded-lg shadow-sm border border-gray-200 z-10">
        <h4 className="text-xs font-semibold text-gray-700 mb-2">
          Grupo ISCO
        </h4>
        <div className="space-y-1">
          {Object.entries(MAJOR_GROUP_COLORS).map(([group, color]) => (
            <div key={group} className="flex items-center gap-2 text-xs">
              <div
                className="w-3 h-3 rounded-full"
                style={{ backgroundColor: color }}
              />
              <span>{MAJOR_GROUP_LABELS[group] || `Grupo ${group}`}</span>
            </div>
          ))}
        </div>
      </div>

      {/* SVG Canvas */}
      <svg
        ref={svgRef}
        width={dimensions.width}
        height={dimensions.height}
        className="bg-gray-50 rounded-lg"
        data-testid="transicion-svg"
      />

      {/* Selected Node Detail */}
      {selectedNode && (
        <div className="absolute bottom-4 left-4 right-4 bg-white rounded-lg shadow-lg border border-gray-200 p-4 z-20 max-h-60 overflow-y-auto">
          <div className="flex items-start justify-between">
            <div className="flex-1">
              <div className="flex items-center gap-2">
                <h3 className="font-semibold text-gray-900">
                  {selectedNode.label}
                </h3>
                <span className="text-xs px-2 py-0.5 bg-gray-100 rounded-full text-gray-600">
                  ISCO {selectedNode.isco_code}
                </span>
              </div>
              <p className="text-xs text-gray-500 mt-1">
                {selectedNode.total_ofertas} ofertas ·{" "}
                {selectedNode.total_skills} skills distintas ·{" "}
                {selectedNode.connections.length} conexiones
              </p>
              {selectedNode.connections.length > 0 && (
                <div className="mt-2 space-y-1">
                  <p className="text-xs font-semibold text-gray-700">
                    Conexiones (por Jaccard):
                  </p>
                  {selectedNode.connections.map((c, i) => (
                    <div key={i} className="text-xs text-gray-600">
                      <span className="font-medium">{c.target}</span>{" "}
                      <span className="text-gray-400">
                        (J={c.jaccard.toFixed(3)})
                      </span>
                      {c.shared.length > 0 && (
                        <span className="text-gray-400 ml-1">
                          — {c.shared.join(", ")}
                        </span>
                      )}
                    </div>
                  ))}
                </div>
              )}
            </div>
            <button
              onClick={() => setSelectedNode(null)}
              className="p-1 hover:bg-gray-100 rounded ml-2"
            >
              <X className="w-4 h-4" />
            </button>
          </div>
        </div>
      )}
    </div>
  );
}

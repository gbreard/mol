'use client';

import React, { useEffect, useRef, useState } from 'react';
import * as d3 from 'd3';

interface HierarchyNode {
  name: string;
  label?: string;
  value?: number;
  children?: HierarchyNode[];
}

interface SunburstProps {
  width?: number;
  height?: number;
  data?: HierarchyNode;
}

// Colores por categoría principal
const categoryColors: Record<string, string> = {
  'S': '#3b82f6',   // Azul - Competencias Técnicas
  'T': '#10b981',   // Verde - Transversales
  'K': '#f59e0b',   // Amarillo - Conocimientos
  'A': '#8b5cf6',   // Violeta - Actitudes
};

type PartitionNode = d3.HierarchyRectangularNode<HierarchyNode>;

// Función para obtener color basado en el código
const getColor = (d: PartitionNode): string => {
  const node = d.data;
  const name = node.name || '';

  // Obtener categoría raíz (S, T, K, A)
  const rootChar = name.charAt(0);

  // Si es el nodo raíz, usar gris
  if (name === 'ESCO Skills') return '#e5e7eb';

  // Color base de la categoría
  const baseColor = categoryColors[rootChar] || '#6b7280';

  // Calcular luminosidad basada en la profundidad
  const depth = d.depth;
  const lightness = Math.min(0.9, 0.4 + (depth * 0.15));

  // Convertir color hex a HSL y ajustar luminosidad
  const color = d3.color(baseColor);
  if (color) {
    const hsl = d3.hsl(color);
    hsl.l = lightness;
    return hsl.formatHex();
  }

  return baseColor;
};

export default function SkillsSunburst({
  width = 700,
  height = 700,
  data: externalData
}: SunburstProps) {
  const svgRef = useRef<SVGSVGElement>(null);
  const [data, setData] = useState<HierarchyNode | null>(externalData || null);
  const [selectedPath, setSelectedPath] = useState<string[]>([]);
  const [tooltip, setTooltip] = useState<{
    visible: boolean;
    x: number;
    y: number;
    content: { name: string; label: string; value: number; percentage: string };
  }>({ visible: false, x: 0, y: 0, content: { name: '', label: '', value: 0, percentage: '' } });

  // Cargar datos si no se proporcionan externamente
  useEffect(() => {
    if (!externalData) {
      fetch('/data/esco_skills_hierarchy.json')
        .then(res => res.json())
        .then(setData)
        .catch(console.error);
    }
  }, [externalData]);

  // Renderizar Sunburst
  useEffect(() => {
    if (!data || !svgRef.current) return;

    const svg = d3.select(svgRef.current);
    svg.selectAll('*').remove();

    const radius = Math.min(width, height) / 2;

    // Crear jerarquía
    const hierarchy = d3.hierarchy<HierarchyNode>(data)
      .sum(d => d.value || 0)
      .sort((a, b) => (b.value || 0) - (a.value || 0));

    // Crear partición radial - esto transforma los nodos a HierarchyRectangularNode
    const partition = d3.partition<HierarchyNode>()
      .size([2 * Math.PI, radius]);

    const root = partition(hierarchy);

    // Crear generador de arcos
    const arc = d3.arc<PartitionNode>()
      .startAngle(d => d.x0)
      .endAngle(d => d.x1)
      .padAngle(d => Math.min((d.x1 - d.x0) / 2, 0.005))
      .padRadius(radius / 2)
      .innerRadius(d => d.y0)
      .outerRadius(d => d.y1 - 1);

    // Contenedor centrado
    const g = svg
      .append('g')
      .attr('transform', `translate(${width / 2},${height / 2})`);

    // Total para calcular porcentajes
    const total = root.value || 1;

    // Obtener todos los nodos excepto la raíz
    const nodes = root.descendants().filter(d => d.depth > 0);

    // Dibujar arcos
    g.selectAll('path')
      .data(nodes)
      .join('path')
      .attr('fill', d => getColor(d))
      .attr('d', d => arc(d) || '')
      .style('cursor', 'pointer')
      .style('stroke', '#fff')
      .style('stroke-width', '0.5px')
      .on('mouseenter', function(event, d) {
        d3.select(this)
          .style('opacity', 0.8)
          .style('stroke-width', '2px');

        const value = d.value || 0;
        const percentage = ((value / total) * 100).toFixed(1);

        setTooltip({
          visible: true,
          x: event.pageX,
          y: event.pageY,
          content: {
            name: d.data.name,
            label: d.data.label || d.data.name,
            value,
            percentage
          }
        });
      })
      .on('mousemove', (event) => {
        setTooltip(prev => ({
          ...prev,
          x: event.pageX,
          y: event.pageY
        }));
      })
      .on('mouseleave', function() {
        d3.select(this)
          .style('opacity', 1)
          .style('stroke-width', '0.5px');
        setTooltip(prev => ({ ...prev, visible: false }));
      })
      .on('click', (event, d) => {
        // Construir path desde raíz hasta este nodo
        const path: string[] = [];
        let current: PartitionNode | null = d;
        while (current && current.depth > 0) {
          path.unshift(current.data.label || current.data.name);
          current = current.parent as PartitionNode | null;
        }
        setSelectedPath(path);
      });

    // Etiquetas para niveles principales
    const labelsData = nodes.filter(d => d.depth === 1 || (d.depth === 2 && (d.x1 - d.x0) > 0.2));

    g.selectAll('text.label')
      .data(labelsData)
      .join('text')
      .attr('class', 'label')
      .attr('transform', d => {
        const x = (d.x0 + d.x1) / 2;
        const y = (d.y0 + d.y1) / 2;
        const angle = (x * 180 / Math.PI) - 90;
        const rotate = angle > 90 ? angle - 180 : angle;
        return `rotate(${rotate}) translate(${y}, 0) rotate(${rotate > 90 || rotate < -90 ? 180 : 0})`;
      })
      .attr('dy', '0.35em')
      .attr('text-anchor', 'middle')
      .style('font-size', d => d.depth === 1 ? '11px' : '9px')
      .style('font-weight', d => d.depth === 1 ? '600' : '400')
      .style('fill', '#1f2937')
      .style('pointer-events', 'none')
      .text(d => {
        const name = d.data.name;
        const arcLength = (d.x1 - d.x0) * ((d.y0 + d.y1) / 2);
        if (arcLength < 30) return '';
        if (name.length > 8) return name.substring(0, 6) + '..';
        return name;
      });

    // Centro con estadísticas
    const innerRadius = root.children?.[0]?.y0 || 50;

    g.append('circle')
      .attr('r', innerRadius - 5)
      .attr('fill', '#f9fafb')
      .attr('stroke', '#e5e7eb');

    g.append('text')
      .attr('text-anchor', 'middle')
      .attr('dy', '-0.5em')
      .style('font-size', '24px')
      .style('font-weight', '700')
      .style('fill', '#1f2937')
      .text(total.toLocaleString());

    g.append('text')
      .attr('text-anchor', 'middle')
      .attr('dy', '1em')
      .style('font-size', '12px')
      .style('fill', '#6b7280')
      .text('skills ESCO');

  }, [data, width, height]);

  return (
    <div className="relative">
      {/* Breadcrumb de selección */}
      {selectedPath.length > 0 && (
        <div className="mb-4 p-3 bg-gray-50 rounded-lg">
          <div className="flex items-center gap-2 text-sm">
            <span className="text-gray-500">Selección:</span>
            {selectedPath.map((item, i) => (
              <React.Fragment key={i}>
                {i > 0 && <span className="text-gray-400">›</span>}
                <span className="font-medium text-gray-700">{item}</span>
              </React.Fragment>
            ))}
            <button
              onClick={() => setSelectedPath([])}
              className="ml-2 text-xs text-blue-600 hover:underline"
            >
              Limpiar
            </button>
          </div>
        </div>
      )}

      {/* SVG del Sunburst */}
      <svg
        ref={svgRef}
        width={width}
        height={height}
        className="mx-auto"
      />

      {/* Tooltip */}
      {tooltip.visible && (
        <div
          className="fixed z-50 bg-white shadow-lg rounded-lg p-3 border pointer-events-none"
          style={{
            left: tooltip.x + 10,
            top: tooltip.y - 10,
            transform: 'translateY(-100%)'
          }}
        >
          <div className="font-semibold text-gray-900">{tooltip.content.name}</div>
          <div className="text-sm text-gray-600">{tooltip.content.label}</div>
          <div className="mt-1 flex gap-3 text-sm">
            <span className="text-blue-600 font-medium">
              {tooltip.content.value.toLocaleString()} skills
            </span>
            <span className="text-gray-500">
              ({tooltip.content.percentage}%)
            </span>
          </div>
        </div>
      )}

      {/* Leyenda */}
      <div className="mt-4 flex justify-center gap-6 text-sm">
        <div className="flex items-center gap-2">
          <div className="w-4 h-4 rounded" style={{ backgroundColor: categoryColors['S'] }}></div>
          <span>Técnicas</span>
        </div>
        <div className="flex items-center gap-2">
          <div className="w-4 h-4 rounded" style={{ backgroundColor: categoryColors['T'] }}></div>
          <span>Transversales</span>
        </div>
        <div className="flex items-center gap-2">
          <div className="w-4 h-4 rounded" style={{ backgroundColor: categoryColors['K'] }}></div>
          <span>Conocimientos</span>
        </div>
      </div>
    </div>
  );
}

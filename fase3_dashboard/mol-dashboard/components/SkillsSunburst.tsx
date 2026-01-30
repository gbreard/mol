'use client';

import React, { useEffect, useRef, useState } from 'react';
import * as d3 from 'd3';

interface HierarchyNode {
  name: string;
  label?: string;
  type?: 'skill' | 'knowledge';
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
  'S1': '#3b82f6',
  'S2': '#3b82f6',
  'S3': '#3b82f6',
  'S4': '#3b82f6',
  'S5': '#3b82f6',
  'S6': '#3b82f6',
  'S7': '#3b82f6',
  'S8': '#3b82f6',
  'T': '#10b981',   // Verde - Transversales
  'T1': '#10b981',
  'T2': '#10b981',
  'T3': '#10b981',
  'T4': '#10b981',
  'T5': '#10b981',
  'T6': '#10b981',
};

// Colores para tipo (anillo externo)
const typeColors: Record<string, string> = {
  'skill': '#6366f1',      // Indigo para skills
  'knowledge': '#f59e0b',  // Amber para knowledge
};

type PartitionNode = d3.HierarchyRectangularNode<HierarchyNode>;

// Función para obtener color basado en el nodo
const getColor = (d: PartitionNode): string => {
  const node = d.data;
  const name = node.name || '';
  const nodeType = node.type;

  // Si es el nodo raíz, usar gris
  if (name === 'ESCO') return '#e5e7eb';

  // Si tiene tipo (skill/knowledge), usar color de tipo
  if (nodeType) {
    return typeColors[nodeType] || '#6b7280';
  }

  // Obtener categoría raíz (S o T)
  const rootChar = name.charAt(0);
  const baseColor = categoryColors[name] || categoryColors[rootChar] || '#6b7280';

  // Calcular luminosidad basada en la profundidad
  const depth = d.depth;
  const lightness = Math.min(0.85, 0.35 + (depth * 0.15));

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
  width = 750,
  height = 750,
  data: externalData
}: SunburstProps) {
  const svgRef = useRef<SVGSVGElement>(null);
  const [data, setData] = useState<HierarchyNode | null>(externalData || null);
  const [selectedPath, setSelectedPath] = useState<string[]>([]);
  const [tooltip, setTooltip] = useState<{
    visible: boolean;
    x: number;
    y: number;
    content: { name: string; label: string; value: number; percentage: string; type?: string };
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

    // Crear partición radial
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
            percentage,
            type: d.data.type
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

    // Etiquetas para niveles 1 y 2
    const labelsData = nodes.filter(d => d.depth <= 2 && (d.x1 - d.x0) > 0.1);

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
        const name = d.data.label || d.data.name;
        const arcLength = (d.x1 - d.x0) * ((d.y0 + d.y1) / 2);
        if (arcLength < 40) return '';
        if (name.length > 12) return name.substring(0, 10) + '..';
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
      .style('font-size', '28px')
      .style('font-weight', '700')
      .style('fill', '#1f2937')
      .text(total.toLocaleString());

    g.append('text')
      .attr('text-anchor', 'middle')
      .attr('dy', '1.2em')
      .style('font-size', '12px')
      .style('fill', '#6b7280')
      .text('competencias ESCO');

  }, [data, width, height]);

  return (
    <div className="relative">
      {/* Breadcrumb de selección */}
      {selectedPath.length > 0 && (
        <div className="mb-4 p-3 bg-gray-50 rounded-lg">
          <div className="flex items-center gap-2 text-sm flex-wrap">
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
          <div className="font-semibold text-gray-900">{tooltip.content.label}</div>
          {tooltip.content.type && (
            <div className={`text-xs font-medium mt-1 ${
              tooltip.content.type === 'skill' ? 'text-indigo-600' : 'text-amber-600'
            }`}>
              {tooltip.content.type === 'skill' ? '🔧 Skill (saber hacer)' : '📚 Conocimiento (saber)'}
            </div>
          )}
          <div className="mt-1 flex gap-3 text-sm">
            <span className="text-blue-600 font-medium">
              {tooltip.content.value.toLocaleString()}
            </span>
            <span className="text-gray-500">
              ({tooltip.content.percentage}%)
            </span>
          </div>
        </div>
      )}

      {/* Leyenda */}
      <div className="mt-6 flex flex-col items-center gap-4">
        {/* Categorías */}
        <div className="flex justify-center gap-6 text-sm">
          <div className="flex items-center gap-2">
            <div className="w-4 h-4 rounded" style={{ backgroundColor: '#3b82f6' }}></div>
            <span>S - Técnicas</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-4 h-4 rounded" style={{ backgroundColor: '#10b981' }}></div>
            <span>T - Transversales</span>
          </div>
        </div>

        {/* Tipos (anillo externo) */}
        <div className="flex justify-center gap-6 text-sm border-t pt-3">
          <div className="flex items-center gap-2">
            <div className="w-4 h-4 rounded" style={{ backgroundColor: '#6366f1' }}></div>
            <span>🔧 Skills (saber hacer)</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-4 h-4 rounded" style={{ backgroundColor: '#f59e0b' }}></div>
            <span>📚 Conocimientos (saber)</span>
          </div>
        </div>
      </div>
    </div>
  );
}

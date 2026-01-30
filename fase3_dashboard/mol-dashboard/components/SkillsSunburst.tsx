'use client';

import React, { useEffect, useRef, useState, useCallback } from 'react';
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

// Colores para tipo (hojas)
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
  const lightness = Math.min(0.85, 0.35 + (depth * 0.12));

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
  width = 800,
  height = 800,
  data: externalData
}: SunburstProps) {
  const svgRef = useRef<SVGSVGElement>(null);
  const [data, setData] = useState<HierarchyNode | null>(externalData || null);
  const [loading, setLoading] = useState(!externalData);
  const [currentPath, setCurrentPath] = useState<string[]>(['ESCO']);
  const [tooltip, setTooltip] = useState<{
    visible: boolean;
    x: number;
    y: number;
    content: { name: string; label: string; value: number; percentage: string; type?: string; path: string[] };
  }>({ visible: false, x: 0, y: 0, content: { name: '', label: '', value: 0, percentage: '', path: [] } });

  // Cargar datos si no se proporcionan externamente
  useEffect(() => {
    if (!externalData) {
      setLoading(true);
      fetch('/data/esco_skills_hierarchy.json')
        .then(res => res.json())
        .then(d => {
          setData(d);
          setLoading(false);
        })
        .catch(err => {
          console.error('Error loading data:', err);
          setLoading(false);
        });
    }
  }, [externalData]);

  // Función para construir path del nodo
  const buildPath = useCallback((d: PartitionNode): string[] => {
    const path: string[] = [];
    let current: PartitionNode | null = d;
    while (current) {
      path.unshift(current.data.label || current.data.name);
      current = current.parent as PartitionNode | null;
    }
    return path;
  }, []);

  // Renderizar Sunburst con zoom
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

    // Guardar posiciones originales para animación
    root.each((d: any) => {
      d.current = d;
    });

    // Crear generador de arcos
    const arc = d3.arc<any>()
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

    // Función para determinar si un arco es visible
    const arcVisible = (d: any) => d.y1 <= 3 * radius && d.y0 >= 0 && d.x1 > d.x0;

    // Función para determinar si una etiqueta es visible
    const labelVisible = (d: any) => d.y1 <= 3 * radius && d.y0 >= 0 && (d.y1 - d.y0) * (d.x1 - d.x0) > 0.03;

    // Función para transformar etiquetas
    const labelTransform = (d: any) => {
      const x = (d.x0 + d.x1) / 2 * 180 / Math.PI;
      const y = (d.y0 + d.y1) / 2;
      return `rotate(${x - 90}) translate(${y},0) rotate(${x < 180 ? 0 : 180})`;
    };

    // Dibujar arcos
    const path = g.selectAll('path')
      .data(root.descendants().filter(d => d.depth > 0))
      .join('path')
      .attr('fill', d => getColor(d))
      .attr('fill-opacity', (d: any) => arcVisible(d.current) ? 1 : 0)
      .attr('pointer-events', (d: any) => arcVisible(d.current) ? 'auto' : 'none')
      .attr('d', (d: any) => arc(d.current))
      .style('cursor', 'pointer')
      .style('stroke', '#fff')
      .style('stroke-width', '0.5px');

    // Hacer clickeables solo los que tienen hijos
    path.filter((d: any) => d.children)
      .style('cursor', 'pointer')
      .on('click', clicked);

    // Tooltip events
    path
      .on('mouseenter', function(event, d) {
        d3.select(this)
          .style('opacity', 0.8)
          .style('stroke-width', '2px');

        const value = d.value || 0;
        const percentage = ((value / total) * 100).toFixed(1);
        const nodePath = buildPath(d);

        setTooltip({
          visible: true,
          x: event.pageX,
          y: event.pageY,
          content: {
            name: d.data.name,
            label: d.data.label || d.data.name,
            value,
            percentage,
            type: d.data.type,
            path: nodePath
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
      });

    // Etiquetas
    const label = g.selectAll('text')
      .data(root.descendants().filter(d => d.depth > 0))
      .join('text')
      .attr('dy', '0.35em')
      .attr('fill-opacity', (d: any) => +labelVisible(d.current))
      .attr('transform', (d: any) => labelTransform(d.current))
      .attr('text-anchor', 'middle')
      .style('font-size', d => d.depth <= 2 ? '10px' : '8px')
      .style('font-weight', d => d.depth === 1 ? '600' : '400')
      .style('fill', '#1f2937')
      .style('pointer-events', 'none')
      .text(d => {
        const name = d.data.label || d.data.name;
        if (name.length > 15) return name.substring(0, 13) + '..';
        return name;
      });

    // Círculo central (clickeable para volver)
    const parent = g.append('circle')
      .datum(root)
      .attr('r', radius / 4)
      .attr('fill', '#f9fafb')
      .attr('stroke', '#e5e7eb')
      .attr('pointer-events', 'all')
      .style('cursor', 'pointer')
      .on('click', clicked);

    // Texto central
    const centerText = g.append('text')
      .attr('text-anchor', 'middle')
      .attr('dy', '-0.3em')
      .style('font-size', '24px')
      .style('font-weight', '700')
      .style('fill', '#1f2937')
      .style('pointer-events', 'none');

    const centerSubtext = g.append('text')
      .attr('text-anchor', 'middle')
      .attr('dy', '1.5em')
      .style('font-size', '11px')
      .style('fill', '#6b7280')
      .style('pointer-events', 'none');

    const centerHint = g.append('text')
      .attr('text-anchor', 'middle')
      .attr('dy', '3em')
      .style('font-size', '10px')
      .style('fill', '#9ca3af')
      .style('pointer-events', 'none');

    // Actualizar texto central
    function updateCenterText(p: any) {
      const value = p.value || 0;
      const name = p.data.label || p.data.name;

      centerText.text(value.toLocaleString());
      centerSubtext.text(name.length > 20 ? name.substring(0, 18) + '..' : name);
      centerHint.text(p.parent ? 'Click para volver' : 'Click para explorar');

      setCurrentPath(buildPath(p));
    }

    updateCenterText(root);

    // Función de click para zoom
    function clicked(event: any, p: any) {
      parent.datum(p.parent || root);

      root.each((d: any) => {
        d.target = {
          x0: Math.max(0, Math.min(1, (d.x0 - p.x0) / (p.x1 - p.x0))) * 2 * Math.PI,
          x1: Math.max(0, Math.min(1, (d.x1 - p.x0) / (p.x1 - p.x0))) * 2 * Math.PI,
          y0: Math.max(0, d.y0 - p.y0),
          y1: Math.max(0, d.y1 - p.y0)
        };
      });

      const t = g.transition().duration(750);

      path.transition(t as any)
        .tween('data', (d: any) => {
          const i = d3.interpolate(d.current, d.target);
          return (t: number) => d.current = i(t);
        })
        .filter(function(d: any) {
          return !!((this as any).getAttribute('fill-opacity')) || arcVisible(d.target);
        })
        .attr('fill-opacity', (d: any) => arcVisible(d.target) ? 1 : 0)
        .attr('pointer-events', (d: any) => arcVisible(d.target) ? 'auto' : 'none')
        .attrTween('d', (d: any) => () => arc(d.current) || '');

      label.filter(function(d: any) {
          return !!((this as any).getAttribute('fill-opacity')) || labelVisible(d.target);
        }).transition(t as any)
        .attr('fill-opacity', (d: any) => +labelVisible(d.target))
        .attrTween('transform', (d: any) => () => labelTransform(d.current));

      updateCenterText(p);
    }

  }, [data, width, height, buildPath]);

  if (loading) {
    return (
      <div className="flex items-center justify-center h-96">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
          <p className="text-gray-600">Cargando taxonomia ESCO...</p>
          <p className="text-sm text-gray-400 mt-1">13,930 competencias</p>
        </div>
      </div>
    );
  }

  return (
    <div className="relative">
      {/* Breadcrumb de navegación */}
      <div className="mb-4 p-3 bg-gray-50 rounded-lg">
        <div className="flex items-center gap-2 text-sm flex-wrap">
          <span className="text-gray-500">Navegacion:</span>
          {currentPath.map((item, i) => (
            <React.Fragment key={i}>
              {i > 0 && <span className="text-gray-400">/</span>}
              <span className={`font-medium ${i === currentPath.length - 1 ? 'text-blue-600' : 'text-gray-700'}`}>
                {item}
              </span>
            </React.Fragment>
          ))}
        </div>
      </div>

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
          className="fixed z-50 bg-white shadow-lg rounded-lg p-3 border pointer-events-none max-w-xs"
          style={{
            left: tooltip.x + 10,
            top: tooltip.y - 10,
            transform: 'translateY(-100%)'
          }}
        >
          <div className="font-semibold text-gray-900 break-words">{tooltip.content.label}</div>
          {tooltip.content.type && (
            <div className={`text-xs font-medium mt-1 ${
              tooltip.content.type === 'skill' ? 'text-indigo-600' : 'text-amber-600'
            }`}>
              {tooltip.content.type === 'skill' ? 'Skill (saber hacer)' : 'Conocimiento (saber)'}
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
          {tooltip.content.path.length > 2 && (
            <div className="mt-2 text-xs text-gray-400 border-t pt-2">
              {tooltip.content.path.slice(1, -1).join(' > ')}
            </div>
          )}
        </div>
      )}

      {/* Instrucciones */}
      <div className="mt-4 text-center text-sm text-gray-500">
        <p>Click en un segmento para hacer zoom. Click en el centro para volver.</p>
      </div>

      {/* Leyenda */}
      <div className="mt-6 flex flex-col items-center gap-4">
        {/* Categorías */}
        <div className="flex justify-center gap-6 text-sm">
          <div className="flex items-center gap-2">
            <div className="w-4 h-4 rounded" style={{ backgroundColor: '#3b82f6' }}></div>
            <span>S - Tecnicas</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-4 h-4 rounded" style={{ backgroundColor: '#10b981' }}></div>
            <span>T - Transversales</span>
          </div>
        </div>

        {/* Tipos (hojas) */}
        <div className="flex justify-center gap-6 text-sm border-t pt-3">
          <div className="flex items-center gap-2">
            <div className="w-4 h-4 rounded" style={{ backgroundColor: '#6366f1' }}></div>
            <span>Skills (saber hacer)</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-4 h-4 rounded" style={{ backgroundColor: '#f59e0b' }}></div>
            <span>Conocimientos (saber)</span>
          </div>
        </div>
      </div>
    </div>
  );
}

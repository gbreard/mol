'use client';

import React, { useEffect, useRef, useState, useCallback } from 'react';
import * as d3 from 'd3';
import SkillsPanel from './SkillsPanel';

interface HierarchyNode {
  name: string;
  label?: string;
  type?: 'skill' | 'knowledge';
  value?: number;
  children?: HierarchyNode[];
}

interface HighlightConfig {
  occupation: { id: string; label: string; isco?: string };
  essential: Set<string>; // L2 codes
  optional: Set<string>;
}

type FilterType = 'all' | 'skills' | 'knowledge';

interface SunburstProps {
  width?: number;
  height?: number;
  data?: HierarchyNode;
  highlightConfig?: HighlightConfig;
  searchTerm?: string;
  filterType?: FilterType;
  onSearchChange?: (term: string) => void;
  onFilterChange?: (filter: FilterType) => void;
}

interface SelectedNode {
  path: string[];
  skills: Array<{ name: string; type: 'skill' | 'knowledge'; isEssential?: boolean; isOptional?: boolean }>;
  occupation?: { label: string; isco?: string };
  totalInCategory: number;
  matchingCount: number;
}

// Colores por categoria principal
const categoryColors: Record<string, string> = {
  'S': '#3b82f6',   // Azul - Competencias Tecnicas
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
  'K': '#8b5cf6',   // Violeta - Conocimientos
  'K1': '#8b5cf6',  // Tecnologia e Informatica
  'K2': '#ec4899',  // Medicina y Salud - Rosa
  'K3': '#6366f1',  // Derecho y Legislacion - Indigo
  'K4': '#f97316',  // Ingenieria y Construccion - Naranja
  'K5': '#14b8a6',  // Negocios y Finanzas - Teal
  'K6': '#22c55e',  // Ciencias Naturales - Verde
  'K7': '#a855f7',  // Industria y Manufactura - Purpura
  'K8': '#f43f5e',  // Arte y Comunicacion - Rose
  'K9': '#0ea5e9',  // Transporte y Logistica - Sky
  'K10': '#84cc16', // Agricultura y Alimentacion - Lime
  'K11': '#eab308', // Educacion y Sociedad - Yellow
  'K12': '#64748b', // Otros Conocimientos - Slate
};

// Colores para tipo (hojas)
const typeColors: Record<string, string> = {
  'skill': '#6366f1',      // Indigo para skills
  'knowledge': '#f59e0b',  // Amber para knowledge
};

type PartitionNode = d3.HierarchyRectangularNode<HierarchyNode>;

// Funcion para obtener color basado en el nodo
const getColor = (d: PartitionNode): string => {
  const node = d.data;
  const name = node.name || '';
  const nodeType = node.type;

  // Si es el nodo raiz, usar gris
  if (name === 'ESCO') return '#e5e7eb';

  // Si tiene tipo (skill/knowledge), usar color de tipo
  if (nodeType) {
    return typeColors[nodeType] || '#6b7280';
  }

  // Obtener categoria raiz (S o T)
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

// Determinar estado de highlight para un nodo
type HighlightState = 'none' | 'essential' | 'optional';

function getHighlightState(
  nodeL2: string,
  config: HighlightConfig | undefined
): HighlightState {
  if (!config) return 'none';

  if (config.essential.has(nodeL2)) return 'essential';
  if (config.optional.has(nodeL2)) return 'optional';

  return 'none';
}

export default function SkillsSunburst({
  width = 700,
  height = 700,
  data: externalData,
  highlightConfig,
  searchTerm = '',
  filterType = 'all'
}: SunburstProps) {
  const svgRef = useRef<SVGSVGElement>(null);
  const [internalData, setInternalData] = useState<HierarchyNode | null>(null);
  const [loading, setLoading] = useState(true);
  const [selectedNode, setSelectedNode] = useState<SelectedNode | null>(null);
  const [tooltip, setTooltip] = useState<{
    visible: boolean;
    x: number;
    y: number;
    content: { name: string; label: string; value: number; percentage: string; type?: string; highlightState?: string; matchesSearch?: boolean };
  }>({ visible: false, x: 0, y: 0, content: { name: '', label: '', value: 0, percentage: '' } });

  // Use external data if provided, otherwise use internally fetched data
  const data = externalData || internalData;

  // Normalize search term for matching
  const normalizedSearch = searchTerm.toLowerCase()
    .normalize('NFD')
    .replace(/[\u0300-\u036f]/g, '');

  // Cargar datos solo si no se proporcionan externamente
  useEffect(() => {
    if (externalData) {
      setLoading(false);
      return;
    }

    setLoading(true);
    fetch('/data/esco_skills_hierarchy.json')
      .then(res => {
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        return res.json();
      })
      .then(d => {
        setInternalData(d);
        setLoading(false);
      })
      .catch(err => {
        console.error('[SUNBURST] Error loading data:', err);
        setLoading(false);
      });
  }, [externalData]);

  // Funcion para construir path del nodo
  const buildPath = useCallback((d: PartitionNode): string[] => {
    const path: string[] = [];
    let current: PartitionNode | null = d;
    while (current) {
      path.unshift(current.data.label || current.data.name);
      current = current.parent as PartitionNode | null;
    }
    return path;
  }, []);

  // Funcion para extraer skills de un nodo (filtrando por ocupación si hay)
  const extractSkills = useCallback((d: PartitionNode, config?: HighlightConfig): {
    skills: Array<{ name: string; type: 'skill' | 'knowledge'; isEssential?: boolean; isOptional?: boolean }>;
    totalInCategory: number;
    matchingCount: number;
  } => {
    const allSkills = d.descendants()
      .filter((node: any) => node.data.type && node.data.value);

    const totalInCategory = allSkills.length;

    // Si hay ocupación seleccionada, filtrar y marcar
    if (config) {
      const matchingSkills = allSkills
        .filter((node: any) => {
          // Obtener L2 del nodo
          let current: PartitionNode | null = node;
          while (current && current.depth > 2) {
            current = current.parent as PartitionNode | null;
          }
          const l2 = current?.data.name || node.data.name;
          return config.essential.has(l2) || config.optional.has(l2);
        })
        .map((node: any) => {
          let current: PartitionNode | null = node;
          while (current && current.depth > 2) {
            current = current.parent as PartitionNode | null;
          }
          const l2 = current?.data.name || node.data.name;
          return {
            name: node.data.label || node.data.name,
            type: node.data.type as 'skill' | 'knowledge',
            isEssential: config.essential.has(l2),
            isOptional: config.optional.has(l2)
          };
        });

      return {
        skills: matchingSkills,
        totalInCategory,
        matchingCount: matchingSkills.length
      };
    }

    // Sin ocupación, devolver todas
    return {
      skills: allSkills.map((node: any) => ({
        name: node.data.label || node.data.name,
        type: node.data.type as 'skill' | 'knowledge'
      })),
      totalInCategory,
      matchingCount: totalInCategory
    };
  }, []);

  // Handler para click en segmento
  const handleSegmentClick = useCallback((d: PartitionNode, config?: HighlightConfig) => {
    const path = buildPath(d);
    const { skills, totalInCategory, matchingCount } = extractSkills(d, config);

    setSelectedNode({
      path,
      skills,
      occupation: config?.occupation ? { label: config.occupation.label, isco: config.occupation.isco } : undefined,
      totalInCategory,
      matchingCount
    });
  }, [buildPath, extractSkills]);

  // Renderizar Sunburst
  useEffect(() => {
    if (!data || !svgRef.current) return;

    const svg = d3.select(svgRef.current);
    svg.selectAll('*').remove();

    const radius = Math.min(width, height) / 2;

    // Crear jerarquia
    const hierarchy = d3.hierarchy<HierarchyNode>(data)
      .sum(d => d.value || 0)
      .sort((a, b) => (b.value || 0) - (a.value || 0));

    // Crear particion radial
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

    // Obtener nodos (excluyendo hojas individuales para mejor rendimiento)
    let nodes = root.descendants().filter(d => d.depth > 0 && d.depth <= 4);

    // Apply filter by type (skills vs knowledge)
    if (filterType !== 'all') {
      // Keep nodes that:
      // 1. Don't have a type (categories)
      // 2. Have the matching type
      // 3. Have descendants with the matching type
      const hasMatchingDescendant = (node: PartitionNode): boolean => {
        if (node.data.type === filterType.slice(0, -1)) return true; // 'skills' -> 'skill'
        if (node.data.type === filterType) return true;
        return node.children?.some(child => hasMatchingDescendant(child as PartitionNode)) || false;
      };

      nodes = nodes.filter(d => {
        // Root categories and subcategories
        if (!d.data.type) return hasMatchingDescendant(d);
        // Leaf nodes
        const nodeType = d.data.type;
        if (filterType === 'skills') return nodeType === 'skill';
        if (filterType === 'knowledge') return nodeType === 'knowledge';
        return true;
      });
    }

    // Function to check if a node or its descendants match the search
    const matchesSearch = (node: PartitionNode): boolean => {
      if (!normalizedSearch) return false;
      const label = (node.data.label || node.data.name || '').toLowerCase()
        .normalize('NFD')
        .replace(/[\u0300-\u036f]/g, '');
      if (label.includes(normalizedSearch)) return true;
      return node.children?.some(child => matchesSearch(child as PartitionNode)) || false;
    };

    // Determinar si hay highlight activo
    const hasHighlight = !!highlightConfig;
    const hasSearch = !!normalizedSearch;

    // Funcion para obtener el L2 code de un nodo (subiendo en la jerarquia si es necesario)
    const getNodeL2 = (d: PartitionNode): string => {
      // El L2 es el nombre del nodo en depth 2, o el padre si estamos mas profundo
      let current: PartitionNode | null = d;
      while (current && current.depth > 2) {
        current = current.parent as PartitionNode | null;
      }
      return current?.data.name || d.data.name;
    };

    // Dibujar arcos
    g.selectAll('path')
      .data(nodes)
      .join('path')
      .attr('fill', d => getColor(d))
      .attr('d', d => arc(d) || '')
      .style('cursor', 'pointer')
      .style('stroke', d => {
        if (!hasHighlight) return '#fff';
        const l2 = getNodeL2(d);
        const state = getHighlightState(l2, highlightConfig);
        switch (state) {
          case 'essential': return '#3b82f6';  // Azul
          case 'optional': return '#93c5fd';   // Azul claro
          default: return '#fff';
        }
      })
      .style('stroke-width', d => {
        if (!hasHighlight) return '0.5px';
        const l2 = getNodeL2(d);
        const state = getHighlightState(l2, highlightConfig);
        if (state === 'none') return '0.5px';
        if (state === 'optional') return '2px';
        return '3px';
      })
      .style('stroke-dasharray', d => {
        if (!hasHighlight) return 'none';
        const l2 = getNodeL2(d);
        const state = getHighlightState(l2, highlightConfig);
        if (state === 'optional') return '4,2';
        return 'none';
      })
      .style('opacity', d => {
        // Search highlighting takes priority
        if (hasSearch) {
          return matchesSearch(d) ? 1 : 0.2;
        }
        if (!hasHighlight) return 1;
        const l2 = getNodeL2(d);
        const state = getHighlightState(l2, highlightConfig);
        return state === 'none' ? 0.25 : 1;
      })
      .on('mouseenter', function(event, d) {
        const nodeL2 = getNodeL2(d);
        const nodeState = getHighlightState(nodeL2, highlightConfig);
        const nodeMatchesSearch = matchesSearch(d);

        let hoverOpacity = 0.8;
        if (hasSearch) {
          hoverOpacity = nodeMatchesSearch ? 0.9 : 0.35;
        } else if (hasHighlight) {
          hoverOpacity = nodeState === 'none' ? 0.4 : 0.9;
        }

        d3.select(this)
          .style('opacity', hoverOpacity)
          .style('stroke-width', '3px');

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
            type: d.data.type,
            highlightState: nodeState !== 'none' ? nodeState : undefined,
            matchesSearch: hasSearch ? nodeMatchesSearch : undefined
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
      .on('mouseleave', function(event, d) {
        const leaveL2 = getNodeL2(d);
        const leaveState = getHighlightState(leaveL2, highlightConfig);
        const nodeMatchesSearch = matchesSearch(d);

        let restoreOpacity = 1;
        if (hasSearch) {
          restoreOpacity = nodeMatchesSearch ? 1 : 0.2;
        } else if (hasHighlight && leaveState === 'none') {
          restoreOpacity = 0.25;
        }

        let restoreStrokeWidth = '0.5px';
        if (hasHighlight && leaveState !== 'none') {
          restoreStrokeWidth = leaveState === 'optional' ? '2px' : '3px';
        }

        d3.select(this)
          .style('opacity', restoreOpacity)
          .style('stroke-width', restoreStrokeWidth);

        setTooltip(prev => ({ ...prev, visible: false }));
      })
      .on('click', function(event, d) {
        event.stopPropagation();
        handleSegmentClick(d, highlightConfig);
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

    // Centro con estadisticas
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

    g.append('text')
      .attr('text-anchor', 'middle')
      .attr('dy', '2.8em')
      .style('font-size', '10px')
      .style('fill', '#9ca3af')
      .text('Click para ver detalle');

  }, [data, width, height, handleSegmentClick, highlightConfig, filterType, normalizedSearch]);

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
          {tooltip.content.highlightState && (
            <div className={`text-xs font-medium mt-1 px-2 py-0.5 rounded inline-block ${
              tooltip.content.highlightState === 'essential' ? 'bg-blue-100 text-blue-700' : 'bg-blue-50 text-blue-600'
            }`}>
              {tooltip.content.highlightState === 'essential' ? 'Competencia esencial' : 'Competencia opcional'}
            </div>
          )}
          {tooltip.content.matchesSearch && (
            <div className="text-xs font-medium mt-1 px-2 py-0.5 rounded inline-block bg-green-100 text-green-700">
              Coincide con busqueda
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
          <div className="mt-2 text-xs text-gray-400">
            Click para ver lista completa
          </div>
        </div>
      )}

      {/* Instrucciones */}
      <div className="mt-4 text-center text-sm text-gray-500">
        <p>Click en cualquier segmento para ver la lista de competencias</p>
      </div>

      {/* Leyenda */}
      <div className="mt-6 flex flex-col items-center gap-4">
        {/* Categorias principales */}
        <div className="flex justify-center gap-6 text-sm">
          <div className="flex items-center gap-2">
            <div className="w-4 h-4 rounded" style={{ backgroundColor: '#3b82f6' }}></div>
            <span>S - Tecnicas</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-4 h-4 rounded" style={{ backgroundColor: '#10b981' }}></div>
            <span>T - Transversales</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-4 h-4 rounded" style={{ backgroundColor: '#8b5cf6' }}></div>
            <span>K - Conocimientos</span>
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

      {/* Panel lateral */}
      {selectedNode && (
        <SkillsPanel
          path={selectedNode.path}
          skills={selectedNode.skills}
          onClose={() => setSelectedNode(null)}
          occupation={selectedNode.occupation}
          totalInCategory={selectedNode.totalInCategory}
          matchingCount={selectedNode.matchingCount}
        />
      )}
    </div>
  );
}

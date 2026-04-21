'use client';

import { useState, useEffect, useMemo, useRef } from 'react';
import { Search, ChevronRight, ChevronDown, List, GitBranch, Briefcase } from 'lucide-react';
import { capitalize } from '@/lib/utils';

interface OccupationInfo {
  id: string;
  label: string;
  isco: string;
}

interface TreeNode {
  label?: string;
  count?: number;
  children?: Record<string, TreeNode>;
  occupations?: { id: string; label: string }[];
}

interface Props {
  occupationsList: OccupationInfo[];
  onSelect: (id: string) => void;
  isOpen: boolean;
  onToggle: (open: boolean) => void;
}

function normalizeForSearch(s: string) {
  return s.toLowerCase().normalize('NFD').replace(/[\u0300-\u036f]/g, '');
}

export default function OccupationTreeSelector({ occupationsList, onSelect, isOpen, onToggle }: Props) {
  const [mode, setMode] = useState<'search' | 'tree'>('search');
  const [searchTerm, setSearchTerm] = useState('');
  const [treeData, setTreeData] = useState<Record<string, TreeNode> | null>(null);
  const [expanded, setExpanded] = useState<Set<string>>(new Set());
  const inputRef = useRef<HTMLInputElement>(null);

  // Load tree data lazily
  useEffect(() => {
    if (mode === 'tree' && !treeData) {
      fetch('/data/isco_tree.json')
        .then(r => r.json())
        .then(d => setTreeData(d))
        .catch(() => {});
    }
  }, [mode, treeData]);

  // Focus input when opening
  useEffect(() => {
    if (isOpen && mode === 'search' && inputRef.current) {
      inputRef.current.focus();
    }
  }, [isOpen, mode]);

  // Search results (no limit)
  const searchResults = useMemo(() => {
    if (!searchTerm.trim() || searchTerm.length < 2) return [];
    const norm = normalizeForSearch(searchTerm);
    return occupationsList
      .filter(occ => {
        const normLabel = normalizeForSearch(occ.label);
        return normLabel.includes(norm) || occ.isco.toLowerCase().includes(norm);
      })
      .slice(0, 50);
  }, [occupationsList, searchTerm]);

  function toggleExpand(key: string) {
    setExpanded(prev => {
      const next = new Set(prev);
      if (next.has(key)) next.delete(key);
      else next.add(key);
      return next;
    });
  }

  function handleSelectOcc(id: string) {
    onSelect(id);
    onToggle(false);
    setSearchTerm('');
  }

  if (!isOpen) return null;

  return (
    <div className="absolute z-30 left-0 right-0 top-full mt-1 bg-white border border-gray-200 rounded-xl shadow-2xl" style={{ maxHeight: 'min(500px, 60vh)', overflow: 'hidden' }}>
      {/* Mode toggle + search */}
      <div className="border-b bg-gray-50 px-3 py-2 flex items-center gap-2">
        <div className="flex bg-gray-200 rounded p-0.5">
          <button
            onClick={() => setMode('search')}
            className={`p-1 rounded ${mode === 'search' ? 'bg-white shadow-sm' : ''}`}
            title="Búsqueda"
          >
            <Search className="w-3.5 h-3.5 text-gray-600" />
          </button>
          <button
            onClick={() => setMode('tree')}
            className={`p-1 rounded ${mode === 'tree' ? 'bg-white shadow-sm' : ''}`}
            title="Árbol ISCO"
          >
            <GitBranch className="w-3.5 h-3.5 text-gray-600" />
          </button>
        </div>
        {mode === 'search' && (
          <input
            ref={inputRef}
            type="text"
            value={searchTerm}
            onChange={e => setSearchTerm(e.target.value)}
            placeholder="Buscar entre 3.045 ocupaciones..."
            className="flex-1 text-sm border-none bg-transparent focus:outline-none"
            autoFocus
          />
        )}
        {mode === 'tree' && (
          <span className="text-xs text-gray-500">Navegar por clasificación ISCO</span>
        )}
      </div>

      {/* Search results */}
      {mode === 'search' && (
        <div className="overflow-y-auto" style={{ maxHeight: 'min(420px, 50vh)' }}>
          {searchTerm.length >= 2 && searchResults.length === 0 && (
            <div className="px-4 py-6 text-center text-sm text-gray-400">No se encontraron ocupaciones</div>
          )}
          {searchTerm.length < 2 && (
            <div className="px-4 py-6 text-center text-xs text-gray-400">Escribí al menos 2 caracteres</div>
          )}
          {searchResults.map(occ => (
            <button
              key={occ.id}
              onClick={() => handleSelectOcc(occ.id)}
              className="w-full text-left px-4 py-2.5 hover:bg-blue-50 border-b border-gray-50 last:border-0"
            >
              <span className="text-sm text-gray-900">{capitalize(occ.label)}</span>
              <span className="text-xs text-gray-400 ml-2">ISCO {occ.isco.replace('C', '')}</span>
            </button>
          ))}
          {searchResults.length === 50 && (
            <div className="px-4 py-2 text-[10px] text-gray-400 text-center bg-gray-50">
              Mostrando 50 resultados. Refiná tu búsqueda.
            </div>
          )}
        </div>
      )}

      {/* Tree view */}
      {mode === 'tree' && (
        <div className="overflow-y-auto" style={{ maxHeight: 'min(420px, 55vh)' }}>
          {!treeData ? (
            <div className="px-4 py-6 text-center text-xs text-gray-400">Cargando árbol...</div>
          ) : (
            <div className="py-1">
              {Object.entries(treeData).filter(([code]) => code !== '0').sort(([a], [b]) => a.localeCompare(b)).map(([d1, g1]) => (
                <TreeLevel
                  key={d1}
                  code={d1}
                  node={g1}
                  depth={0}
                  expanded={expanded}
                  onToggle={toggleExpand}
                  onSelectOcc={handleSelectOcc}
                />
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
}

function TreeLevel({
  code, node, depth, expanded, onToggle, onSelectOcc
}: {
  code: string;
  node: TreeNode;
  depth: number;
  expanded: Set<string>;
  onToggle: (key: string) => void;
  onSelectOcc: (id: string) => void;
}) {
  const isExpanded = expanded.has(code);
  const hasChildren = node.children && Object.keys(node.children).length > 0;
  const hasOccupations = node.occupations && node.occupations.length > 0;
  const pl = depth * 16 + 8;

  const colors = [
    'text-blue-700 bg-blue-50',
    'text-purple-700 bg-purple-50',
    'text-teal-700 bg-teal-50',
    'text-gray-700 bg-gray-50',
  ];
  const colorClass = colors[Math.min(depth, colors.length - 1)];

  return (
    <div>
      {/* Node button */}
      {(hasChildren || hasOccupations) && (
        <button
          onClick={() => onToggle(code)}
          className={`w-full text-left flex items-center gap-1.5 py-1.5 px-2 hover:bg-gray-100 transition-colors ${depth === 0 ? 'font-medium' : ''}`}
          style={{ paddingLeft: `${pl}px` }}
        >
          {hasChildren ? (
            isExpanded ? <ChevronDown className="w-3 h-3 text-gray-400 shrink-0" /> : <ChevronRight className="w-3 h-3 text-gray-400 shrink-0" />
          ) : (
            <List className="w-3 h-3 text-gray-300 shrink-0" />
          )}
          <span className={`text-[10px] px-1.5 py-0.5 rounded font-mono shrink-0 ${colorClass}`}>{code}</span>
          <span className={`text-xs ${depth === 0 ? 'text-gray-900 font-medium' : 'text-gray-700'} flex-1 leading-snug`}>
            {node.label || `Grupo ${code}`}
          </span>
          <span className="text-[10px] text-gray-300 shrink-0">{node.count || ''}</span>
        </button>
      )}

      {/* Expanded children */}
      {isExpanded && hasChildren && (
        <div>
          {Object.entries(node.children!).sort(([a], [b]) => a.localeCompare(b)).map(([childCode, child]) => (
            <TreeLevel
              key={childCode}
              code={childCode}
              node={child}
              depth={depth + 1}
              expanded={expanded}
              onToggle={onToggle}
              onSelectOcc={onSelectOcc}
            />
          ))}
        </div>
      )}

      {/* Occupations (leaf level) */}
      {isExpanded && hasOccupations && (
        <div>
          {node.occupations!.map(occ => (
            <button
              key={occ.id}
              onClick={() => onSelectOcc(occ.id)}
              className="w-full text-left flex items-center gap-1.5 py-1.5 px-2 hover:bg-blue-50 transition-colors"
              style={{ paddingLeft: `${pl + 20}px` }}
            >
              <Briefcase className="w-3 h-3 text-blue-400 shrink-0" />
              <span className="text-xs text-gray-800">{capitalize(occ.label)}</span>
            </button>
          ))}
        </div>
      )}
    </div>
  );
}

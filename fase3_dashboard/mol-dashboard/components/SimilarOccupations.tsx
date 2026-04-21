'use client';

import { useState, useEffect, useMemo } from 'react';
import { ArrowRight, Users, Briefcase, ExternalLink, ArrowUpDown, Eye, EyeOff, Loader2, TrendingUp, TrendingDown, Minus } from 'lucide-react';
import { createBrowserClient } from '@supabase/ssr';
import { SimilarOccupation } from '@/lib/types';
import { capitalize } from '@/lib/utils';

let _sb: ReturnType<typeof createBrowserClient> | null = null;
function getSb() {
  if (!_sb) _sb = createBrowserClient(process.env.NEXT_PUBLIC_SUPABASE_URL!, process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!);
  return _sb;
}

interface SimilarOccupationsProps {
  occupations: SimilarOccupation[];
  ofertasCountMap?: Record<string, number>;
  onSelect?: (occupationId: string) => void;
  onCompare?: (occupationId: string) => void;
  onViewOfertas?: (isco: string, label: string) => void;
  maxItems?: number;
  showQuantitySelector?: boolean;
}

function normalizeIsco(isco: string): string {
  return isco.startsWith('C') ? isco.substring(1) : isco;
}

function getOfertasCount(isco: string, countMap: Record<string, number>): number {
  return countMap[isco] || countMap[normalizeIsco(isco)] || 0;
}

type SortMode = 'similar' | 'ofertas' | 'creciendo' | 'oportunidad';

interface TrendInfo {
  trend_label: string;
  ofertas_total: number;
  suficiente: boolean;
}

export default function SimilarOccupations({
  occupations,
  ofertasCountMap = {},
  onSelect,
  onCompare,
  onViewOfertas,
  maxItems = 10,
  showQuantitySelector = false
}: SimilarOccupationsProps) {
  const [displayCount, setDisplayCount] = useState(maxItems);
  const [sortMode, setSortMode] = useState<SortMode>('similar');
  const [onlyWithOffers, setOnlyWithOffers] = useState(false);
  const [trendMap, setTrendMap] = useState<Record<string, TrendInfo>>({});
  const [trendLoading, setTrendLoading] = useState(false);

  // Load trends for all similar occupation ISCOs
  useEffect(() => {
    if (occupations.length === 0) return;
    const iscos = [...new Set(occupations.map(o => normalizeIsco(o.isco)))];
    if (iscos.length === 0) return;

    setTrendLoading(true);
    getSb()
      .from('isco_demand_trend')
      .select('isco_code, trend_label, ofertas_total, suficiente')
      .in('isco_code', iscos)
      .then(({ data }) => {
        if (data) {
          const map: Record<string, TrendInfo> = {};
          for (const t of data) map[t.isco_code] = t;
          setTrendMap(map);
        }
        setTrendLoading(false);
      });
  }, [occupations]);

  const hasOfertasData = Object.keys(ofertasCountMap).length > 0;

  // Sort + filter
  const processed = useMemo(() => {
    let list = [...occupations];

    // Filter
    if (onlyWithOffers && hasOfertasData) {
      list = list.filter(o => getOfertasCount(o.isco, ofertasCountMap) > 0);
    }

    // Sort
    list.sort((a, b) => {
      const aIsco = normalizeIsco(a.isco);
      const bIsco = normalizeIsco(b.isco);
      const aOfertas = getOfertasCount(a.isco, ofertasCountMap);
      const bOfertas = getOfertasCount(b.isco, ofertasCountMap);
      const aTrend = trendMap[aIsco];
      const bTrend = trendMap[bIsco];

      switch (sortMode) {
        case 'ofertas':
          if (bOfertas !== aOfertas) return bOfertas - aOfertas;
          return b.jaccard - a.jaccard;
        case 'creciendo': {
          const aScore = aTrend?.trend_label === 'creciendo' ? 2 : aTrend?.trend_label === 'estable' ? 1 : 0;
          const bScore = bTrend?.trend_label === 'creciendo' ? 2 : bTrend?.trend_label === 'estable' ? 1 : 0;
          if (bScore !== aScore) return bScore - aScore;
          return bOfertas - aOfertas;
        }
        case 'oportunidad': {
          const aOp = a.jaccard * Math.log2(aOfertas + 1);
          const bOp = b.jaccard * Math.log2(bOfertas + 1);
          return bOp - aOp;
        }
        default: // similar
          return b.jaccard - a.jaccard;
      }
    });

    return list;
  }, [occupations, sortMode, onlyWithOffers, ofertasCountMap, trendMap, hasOfertasData]);

  const displayed = processed.slice(0, displayCount);
  const hiddenCount = processed.length - displayed.length;
  const withOffersCount = occupations.filter(o => getOfertasCount(o.isco, ofertasCountMap) > 0).length;
  const withoutOffersCount = occupations.length - withOffersCount;

  if (occupations.length === 0) {
    return (
      <div className="text-center py-8 text-gray-500">
        <Users className="w-8 h-8 mx-auto mb-2 opacity-50" />
        <p>No hay ocupaciones similares</p>
      </div>
    );
  }

  function TrendBadge({ isco }: { isco: string }) {
    const trend = trendMap[normalizeIsco(isco)];
    if (!trend || !trend.suficiente) return null;
    const label = trend.trend_label;
    if (label === 'creciendo') return <span className="text-[10px] text-green-600 font-medium flex items-center gap-0.5"><TrendingUp className="w-3 h-3" />Crece</span>;
    if (label === 'cayendo') return <span className="text-[10px] text-red-500 font-medium flex items-center gap-0.5"><TrendingDown className="w-3 h-3" />Cae</span>;
    return <span className="text-[10px] text-gray-400 font-medium flex items-center gap-0.5"><Minus className="w-3 h-3" />Estable</span>;
  }

  return (
    <div className="space-y-4">
      {/* Header */}
      <div>
        <h3 className="font-semibold text-gray-900 flex items-center gap-2 mb-1">
          <Users className="w-5 h-5 text-purple-600" />
          Ocupaciones Similares
        </h3>
        <p className="text-xs text-gray-500">
          {withOffersCount} con ofertas activas · {withoutOffersCount} sin ofertas
        </p>
      </div>

      {/* Controls */}
      <div className="flex items-center gap-2 flex-wrap">
        {/* Sort */}
        <div className="flex items-center gap-1">
          <ArrowUpDown className="w-3 h-3 text-gray-400" />
          {([
            { id: 'similar' as SortMode, label: 'Más similar' },
            { id: 'ofertas' as SortMode, label: 'Más ofertas' },
            { id: 'creciendo' as SortMode, label: 'Creciendo' },
            { id: 'oportunidad' as SortMode, label: 'Oportunidad' },
          ]).map(s => (
            <button
              key={s.id}
              onClick={() => setSortMode(s.id)}
              className={`text-[10px] px-2 py-0.5 rounded-full transition-colors ${sortMode === s.id ? 'bg-purple-100 text-purple-700 font-medium' : 'text-gray-400 hover:text-gray-600'}`}
            >
              {s.label}
            </button>
          ))}
        </div>

        {/* Toggle offers */}
        {hasOfertasData && withoutOffersCount > 0 && (
          <button
            onClick={() => setOnlyWithOffers(v => !v)}
            className="flex items-center gap-1 text-[10px] text-gray-500 hover:text-gray-700 ml-auto"
          >
            {onlyWithOffers ? <Eye className="w-3 h-3" /> : <EyeOff className="w-3 h-3" />}
            {onlyWithOffers ? 'Ver todas' : 'Solo con ofertas'}
          </button>
        )}

        {/* Quantity */}
        {showQuantitySelector && (
          <select
            value={displayCount}
            onChange={(e) => setDisplayCount(Number(e.target.value))}
            className="text-[10px] border border-gray-200 rounded px-1.5 py-0.5 bg-white text-gray-500"
          >
            <option value={10}>10</option>
            <option value={20}>20</option>
            <option value={30}>30</option>
          </select>
        )}
      </div>

      {trendLoading && (
        <div className="flex items-center gap-1 text-gray-400">
          <Loader2 className="w-3 h-3 animate-spin" />
          <span className="text-[10px]">Cargando tendencias...</span>
        </div>
      )}

      {/* List */}
      <ul className="space-y-2">
        {displayed.map((occ, index) => {
          const percentMatch = Math.round(occ.jaccard * 100);
          const ofertasCount = getOfertasCount(occ.isco, ofertasCountMap);

          return (
            <li key={occ.id} className="bg-gray-50 hover:bg-gray-100 rounded-lg p-3 transition-colors">
              {/* Row 1: name (no truncate — wraps to 2 lines) */}
              <div className="flex items-start justify-between gap-2">
                <div className="flex-1 min-w-0">
                  <div className="flex items-start gap-2">
                    <span className="text-gray-400 text-xs font-mono w-4 shrink-0 mt-0.5">{index + 1}.</span>
                    <span className="text-sm font-medium text-gray-900 leading-snug">
                      {capitalize(occ.label)}
                    </span>
                  </div>
                </div>
                {/* Similarity bar */}
                <div className="flex items-center gap-1.5 shrink-0">
                  <div className="w-14 h-1.5 bg-gray-200 rounded-full overflow-hidden">
                    <div className="h-full bg-purple-500 rounded-full" style={{ width: `${percentMatch}%` }} />
                  </div>
                  <span className="text-xs font-semibold text-purple-700 w-7 text-right">{percentMatch}%</span>
                </div>
              </div>

              {/* Row 2: ISCO + badges + trend */}
              <div className="flex items-center gap-2 mt-1.5 ml-6 flex-wrap">
                <span className="text-[10px] font-mono text-gray-400">ISCO {normalizeIsco(occ.isco)}</span>
                <span className="text-[10px] text-gray-400">{occ.shared} skills compartidas</span>
                {hasOfertasData && ofertasCount > 0 && (
                  <span className="inline-flex items-center gap-0.5 bg-green-100 text-green-700 text-[10px] px-1.5 py-0.5 rounded-full font-medium">
                    <Briefcase className="w-2.5 h-2.5" />
                    {ofertasCount}
                  </span>
                )}
                {hasOfertasData && ofertasCount === 0 && (
                  <span className="text-[10px] text-gray-300">Sin ofertas</span>
                )}
                <TrendBadge isco={occ.isco} />
              </div>

              {/* Row 3: actions */}
              <div className="flex items-center gap-3 mt-1.5 ml-6">
                {onSelect && (
                  <button
                    onClick={() => { onSelect(occ.id); window.scrollTo({ top: 0, behavior: 'smooth' }); }}
                    className="text-[10px] text-blue-600 hover:text-blue-700 font-medium"
                  >
                    Ver detalle
                  </button>
                )}
                {onCompare && (
                  <button onClick={() => onCompare(occ.id)} className="text-[10px] text-purple-600 hover:text-purple-700 font-medium">
                    Comparar
                  </button>
                )}
                {hasOfertasData && ofertasCount > 0 && onViewOfertas && (
                  <button
                    onClick={() => onViewOfertas(normalizeIsco(occ.isco), occ.label)}
                    className="text-[10px] text-green-600 hover:text-green-700 font-medium flex items-center gap-0.5"
                  >
                    Ver {ofertasCount} oferta{ofertasCount !== 1 ? 's' : ''}
                    <ExternalLink className="w-2.5 h-2.5" />
                  </button>
                )}
              </div>
            </li>
          );
        })}
      </ul>

      {hiddenCount > 0 && (
        <p className="text-[10px] text-gray-400 text-center">
          Mostrando {displayed.length} de {processed.length}
          {onlyWithOffers && ` (${withoutOffersCount} sin ofertas ocultas)`}
        </p>
      )}
    </div>
  );
}

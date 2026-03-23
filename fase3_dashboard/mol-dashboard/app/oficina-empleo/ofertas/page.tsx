"use client";

import { useState, useEffect, Suspense } from "react";
import { useSearchParams } from "next/navigation";
import {
  Briefcase, Target, GraduationCap, Loader2, ExternalLink,
  MapPin, Clock, Building2, ArrowLeft,
} from "lucide-react";
import Link from "next/link";

type Tab = "ofertas" | "capacitacion";

interface MatchingOffer {
  id_oferta: number;
  titulo: string;
  empresa: string;
  provincia: string;
  localidad: string;
  modalidad: string;
  fecha_publicacion: string;
  url_oferta: string;
  match_score: number;
  skills_cubiertas: string[];
  skills_gap: string[];
}

interface TrainingSuggestion {
  skill_label: string;
  courses: {
    id: number;
    name: string;
    certificacion: string;
    duracion: string;
    modalidad: string;
    covers_skills: string[];
    url?: string;
  }[];
}

interface TransitionOcc {
  ocupacion_label: string;
  isco: string;
  trend_pct: number;
  match_score: number;
  skills_gap: string[];
  estimated_months: number;
}

function OfertasContent() {
  const searchParams = useSearchParams();
  const iscoParam = searchParams.get("isco") || "";
  const skillsParam = searchParams.get("skills") || "";

  const [tab, setTab] = useState<Tab>("ofertas");
  const [offers, setOffers] = useState<MatchingOffer[]>([]);
  const [training, setTraining] = useState<{ by_gap: TrainingSuggestion[]; transition_demand: TransitionOcc[] } | null>(null);
  const [loading, setLoading] = useState(true);
  const [page, setPage] = useState(1);
  const [total, setTotal] = useState(0);
  const [provinciaFilter, setProvinciaFilter] = useState("");
  const [modalidadFilter, setModalidadFilter] = useState("");

  const workerSkills = skillsParam ? skillsParam.split(",").map(s => s.trim()) : [];

  useEffect(() => { loadOffers(); loadTraining(); }, [iscoParam, skillsParam]);

  async function loadOffers() {
    setLoading(true);
    try {
      const params = new URLSearchParams();
      if (iscoParam) params.set("isco_codes", iscoParam);
      if (skillsParam) params.set("skills", skillsParam);
      if (provinciaFilter) params.set("provincia", provinciaFilter);
      if (modalidadFilter) params.set("modalidad", modalidadFilter);
      params.set("page", String(page));

      const res = await fetch(`/api/matching-offers?${params}`);
      if (res.ok) {
        const data = await res.json();
        setOffers(data.offers || []);
        setTotal(data.total || 0);
      }
    } catch {} finally { setLoading(false); }
  }

  async function loadTraining() {
    try {
      const res = await fetch(`/api/training-suggestions`);
      if (res.ok) setTraining(await res.json());
    } catch {}
  }

  useEffect(() => {
    if (tab === "ofertas") loadOffers();
  }, [provinciaFilter, modalidadFilter, page]);

  const tabs: { id: Tab; label: string; icon: typeof Target; count?: number }[] = [
    { id: "ofertas", label: "Ofertas laborales", icon: Briefcase, count: total },
    { id: "capacitacion", label: "Capacitacion sugerida", icon: GraduationCap },
  ];

  return (
    <div className="max-w-5xl mx-auto px-4 py-8">
      {/* Header */}
      <div className="flex items-center gap-3 mb-6">
        <Link href="/oficina-empleo/perfil" className="text-gray-400 hover:text-gray-600">
          <ArrowLeft className="w-5 h-5" />
        </Link>
        <Briefcase className="w-7 h-7 text-teal-600" />
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Ofertas Coincidentes</h1>
          <p className="text-sm text-gray-500">
            {workerSkills.length > 0 ? `${workerSkills.length} skills del perfil` : "Selecciona un perfil para ver ofertas personalizadas"}
            {iscoParam && ` · ISCO ${iscoParam}`}
          </p>
        </div>
      </div>

      {/* Tabs */}
      <div className="flex gap-1 border-b border-gray-200 mb-6">
        {tabs.map(t => {
          const Icon = t.icon;
          return (
            <button key={t.id} onClick={() => setTab(t.id)}
              className={`flex items-center gap-2 px-4 py-2.5 text-sm font-medium border-b-2 transition-colors ${
                tab === t.id ? "border-teal-600 text-teal-600" : "border-transparent text-gray-500 hover:text-gray-700"
              }`}>
              <Icon className="w-4 h-4" />
              {t.label}
              {t.count !== undefined && t.count > 0 && (
                <span className="text-xs bg-teal-100 text-teal-700 px-1.5 py-0.5 rounded-full">{t.count}</span>
              )}
            </button>
          );
        })}
      </div>

      {/* TAB: Ofertas laborales */}
      {tab === "ofertas" && (
        <div className="space-y-4">
          <div className="flex gap-3 flex-wrap">
            <select value={provinciaFilter} onChange={e => { setProvinciaFilter(e.target.value); setPage(1); }}
              className="border rounded-lg px-3 py-2 text-sm">
              <option value="">Todas las provincias</option>
              <option value="Capital Federal">CABA</option>
              <option value="Buenos Aires">Buenos Aires</option>
              <option value="Córdoba">Cordoba</option>
              <option value="Santa Fe">Santa Fe</option>
              <option value="Mendoza">Mendoza</option>
            </select>
            <select value={modalidadFilter} onChange={e => { setModalidadFilter(e.target.value); setPage(1); }}
              className="border rounded-lg px-3 py-2 text-sm">
              <option value="">Todas las modalidades</option>
              <option value="remoto">Remoto</option>
              <option value="presencial">Presencial</option>
              <option value="hibrido">Hibrido</option>
            </select>
            <span className="text-sm text-gray-500 self-center">{total} ofertas</span>
          </div>

          {loading ? (
            <div className="py-12 text-center"><Loader2 className="w-8 h-8 animate-spin text-teal-600 mx-auto mb-3" /><p className="text-gray-500">Buscando ofertas...</p></div>
          ) : offers.length === 0 ? (
            <div className="py-12 text-center text-gray-400">
              <Briefcase className="w-12 h-12 mx-auto mb-3 opacity-30" />
              <p>No se encontraron ofertas coincidentes.</p>
              <p className="text-xs mt-1">Intenta ampliar los filtros o agregar mas competencias.</p>
              <Link href="/oficina-empleo/perfil" className="inline-flex items-center gap-2 mt-4 text-sm text-teal-600 hover:text-teal-700 font-medium">
                <ArrowLeft className="w-4 h-4" /> Volver al perfil
              </Link>
            </div>
          ) : (
            <div className="space-y-3">
              {offers.map(offer => (
                <div key={offer.id_oferta} className="bg-white rounded-xl border border-gray-200 p-5 hover:shadow-md transition-shadow">
                  <div className="flex items-start justify-between gap-4">
                    <div className="flex-1 min-w-0">
                      <h3 className="font-semibold text-gray-900">{offer.titulo}</h3>
                      <div className="flex items-center gap-3 text-sm text-gray-500 mt-1 flex-wrap">
                        <span className="flex items-center gap-1"><Building2 className="w-3.5 h-3.5" />{offer.empresa}</span>
                        <span className="flex items-center gap-1"><MapPin className="w-3.5 h-3.5" />{offer.provincia}</span>
                        {offer.modalidad && <span>{offer.modalidad}</span>}
                        {offer.fecha_publicacion && <span className="flex items-center gap-1"><Clock className="w-3.5 h-3.5" />{formatDate(offer.fecha_publicacion)}</span>}
                      </div>
                    </div>
                    <div className={`w-14 h-14 rounded-full flex items-center justify-center text-sm font-bold flex-shrink-0 ${
                      offer.match_score >= 70 ? "bg-green-100 text-green-700" : offer.match_score >= 40 ? "bg-amber-100 text-amber-700" : "bg-gray-100 text-gray-500"
                    }`}>{offer.match_score}%</div>
                  </div>
                  <div className="mt-3 space-y-1">
                    {offer.skills_cubiertas.length > 0 && (
                      <div className="flex flex-wrap gap-1">
                        <span className="text-xs text-green-600 font-medium mr-1">Tenes:</span>
                        {offer.skills_cubiertas.map(s => <span key={s} className="text-xs bg-green-50 text-green-700 px-2 py-0.5 rounded-full">{s}</span>)}
                      </div>
                    )}
                    {offer.skills_gap.length > 0 && (
                      <div className="flex flex-wrap gap-1">
                        <span className="text-xs text-red-500 font-medium mr-1">Te faltan:</span>
                        {offer.skills_gap.map(s => <span key={s} className="text-xs bg-red-50 text-red-600 px-2 py-0.5 rounded-full">{s}</span>)}
                      </div>
                    )}
                  </div>
                  {offer.url_oferta && (
                    <div className="mt-3 pt-3 border-t border-gray-100">
                      <a href={offer.url_oferta} target="_blank" rel="noopener noreferrer"
                        className="text-sm text-teal-600 hover:text-teal-700 font-medium inline-flex items-center gap-1">
                        Ver oferta <ExternalLink className="w-3.5 h-3.5" />
                      </a>
                    </div>
                  )}
                </div>
              ))}
              {total > offers.length && (
                <button onClick={() => setPage(p => p + 1)}
                  className="w-full py-3 text-sm text-teal-600 hover:bg-teal-50 rounded-lg font-medium">Cargar mas</button>
              )}
            </div>
          )}
        </div>
      )}

      {/* TAB: Capacitación */}
      {tab === "capacitacion" && (
        <div className="space-y-6">
          {!training ? (
            <div className="py-12 text-center"><Loader2 className="w-8 h-8 animate-spin text-teal-600 mx-auto mb-3" /><p className="text-gray-500">Buscando cursos...</p></div>
          ) : (training.by_gap || []).length > 0 ? (
            <>
              {training.by_gap.map((gap, i) => (
                <div key={i} className="bg-white rounded-xl border border-gray-200 overflow-hidden">
                  <div className="px-5 py-3 bg-red-50 border-b border-red-100">
                    <span className="text-sm font-medium text-red-700">Te falta: {gap.skill_label}</span>
                  </div>
                  <div className="divide-y">
                    {gap.courses.map((course, j) => (
                      <div key={j} className="px-5 py-4 hover:bg-gray-50">
                        <div className="font-medium text-gray-900 text-sm">{course.name}</div>
                        <div className="flex items-center gap-3 text-xs text-gray-500 mt-1">
                          {course.certificacion && <span>{course.certificacion}</span>}
                          {course.duracion && <span>{course.duracion}</span>}
                          {course.modalidad && <span>{course.modalidad}</span>}
                        </div>
                        {course.covers_skills.length > 0 && (
                          <div className="flex flex-wrap gap-1 mt-2">
                            <span className="text-xs text-gray-400">Cubre:</span>
                            {course.covers_skills.map(s => <span key={s} className="text-xs bg-blue-50 text-blue-600 px-1.5 py-0.5 rounded">{s}</span>)}
                          </div>
                        )}
                      </div>
                    ))}
                  </div>
                </div>
              ))}

              {(training.transition_demand || []).length > 0 && (
                <div className="bg-teal-50 border border-teal-200 rounded-xl p-5">
                  <h3 className="font-semibold text-teal-900 mb-3">Transicion laboral sugerida</h3>
                  <div className="space-y-3">
                    {training.transition_demand.map((t, i) => (
                      <div key={i} className="flex items-center gap-4 bg-white rounded-lg p-4 border border-teal-100">
                        <div className="flex-1">
                          <div className="font-medium text-gray-900">{t.ocupacion_label}</div>
                          <div className="text-xs text-gray-500">Tendencia +{t.trend_pct}% · Faltan: {t.skills_gap.join(", ")}</div>
                        </div>
                        <div className="text-right">
                          <div className="text-sm font-bold text-teal-700">{t.match_score}%</div>
                          <div className="text-xs text-gray-400">~{t.estimated_months} meses</div>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </>
          ) : (
            <div className="py-8 text-center text-gray-400">
              <GraduationCap className="w-12 h-12 mx-auto mb-3 opacity-30" />
              <p className="text-sm">Sin sugerencias de capacitacion por ahora.</p>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

function formatDate(ts: string): string {
  try {
    const d = new Date(ts);
    const diff = Math.round((Date.now() - d.getTime()) / 86400000);
    if (diff === 0) return "Hoy";
    if (diff === 1) return "Ayer";
    if (diff < 7) return `Hace ${diff} dias`;
    return d.toLocaleDateString("es-AR", { day: "2-digit", month: "short" });
  } catch { return ""; }
}

// Wrap with Suspense for useSearchParams
export default function OfertasPage() {
  return (
    <Suspense fallback={<div className="py-12 text-center"><Loader2 className="w-8 h-8 animate-spin text-teal-600 mx-auto" /></div>}>
      <OfertasContent />
    </Suspense>
  );
}

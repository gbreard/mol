"use client";

import { useState } from "react";
import dynamic from "next/dynamic";
import { FileText, Cpu, Globe, Briefcase, Zap, Scissors } from "lucide-react";

// Lazy-load each editor to avoid loading all at once
const ReglasEditor = dynamic(() => import("../reglas/page"), { ssr: false });
const NlpInferenceEditor = dynamic(() => import("../nlp-inference/page"), { ssr: false });
const SinonimosEditor = dynamic(() => import("../sinonimos/page"), { ssr: false });
const OficiosEditor = dynamic(() => import("../oficios/page"), { ssr: false });
const EditoresGenerico = dynamic(() => import("../editores/page"), { ssr: false });

type Tab = "reglas" | "nlp" | "sinonimos" | "oficios" | "skills" | "limpieza";

const TABS: { id: Tab; label: string; icon: typeof FileText; count?: string }[] = [
  { id: "reglas", label: "Reglas Matching", icon: FileText, count: "300" },
  { id: "nlp", label: "NLP Inference", icon: Cpu, count: "~50" },
  { id: "sinonimos", label: "Sinonimos ARG", icon: Globe, count: "17" },
  { id: "oficios", label: "Oficios ARG", icon: Briefcase, count: "170" },
  { id: "skills", label: "Skills Rules", icon: Zap, count: "27" },
  { id: "limpieza", label: "Limpieza Titulos", icon: Scissors, count: "~30" },
];

export default function DiccionariosPage() {
  const [activeTab, setActiveTab] = useState<Tab>("reglas");

  return (
    <div className="flex flex-col h-full">
      {/* Tab bar */}
      <div className="border-b border-gray-200 bg-white px-6 pt-4">
        <div className="flex items-center justify-between mb-3">
          <div>
            <h1 className="text-xl font-bold text-gray-900">Diccionarios del Pipeline</h1>
            <p className="text-gray-500 text-xs mt-0.5">Reglas y configuraciones que la fabrica usa para procesar</p>
          </div>
        </div>
        <div className="flex gap-1 overflow-x-auto">
          {TABS.map((tab) => {
            const Icon = tab.icon;
            return (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`flex items-center gap-1.5 px-3 py-2 text-sm font-medium border-b-2 transition-colors whitespace-nowrap ${
                  activeTab === tab.id
                    ? "border-blue-600 text-blue-600"
                    : "border-transparent text-gray-500 hover:text-gray-700"
                }`}
              >
                <Icon className="w-3.5 h-3.5" />
                {tab.label}
                {tab.count && (
                  <span className="text-xs bg-gray-100 text-gray-500 px-1.5 py-0.5 rounded-full">{tab.count}</span>
                )}
              </button>
            );
          })}
        </div>
      </div>

      {/* Tab content — each editor is a full page component rendered inline */}
      <div className="flex-1 overflow-y-auto">
        {activeTab === "reglas" && <ReglasEditor />}
        {activeTab === "nlp" && <NlpInferenceEditor />}
        {activeTab === "sinonimos" && <SinonimosEditor />}
        {activeTab === "oficios" && <OficiosEditor />}
        {/* Skills rules and limpieza use the generic editor */}
        {(activeTab === "skills" || activeTab === "limpieza") && <EditoresGenerico />}
      </div>
    </div>
  );
}

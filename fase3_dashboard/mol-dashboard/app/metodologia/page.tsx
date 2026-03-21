import Link from "next/link";
import { Database, Brain, Target, GitMerge } from "lucide-react";

const sections = [
  {
    icon: Database,
    title: "Fuentes de datos",
    content:
      "El MOL recopila ofertas laborales de los principales portales de empleo de Argentina mediante procesos automatizados de scraping. Las ofertas se actualizan diariamente y se procesan para extraer informacion estructurada.",
  },
  {
    icon: Brain,
    title: "Procesamiento NLP",
    content:
      "Cada oferta es analizada mediante modelos de procesamiento de lenguaje natural (NLP) que extraen informacion clave: titulo limpio, ubicacion, modalidad, seniority, area funcional, tareas, requisitos de experiencia y competencias requeridas.",
  },
  {
    icon: Target,
    title: "Clasificacion ESCO / ISCO",
    content:
      "Las ofertas se clasifican segun la taxonomia europea ESCO (European Skills, Competences, Qualifications and Occupations) y su codigo ISCO asociado. El sistema utiliza un enfoque hibrido: reglas de negocio para casos frecuentes y matching semantico con embeddings para el resto.",
  },
  {
    icon: GitMerge,
    title: "Matching y validacion",
    content:
      "El proceso de matching combina multiples senales: skills extraidas, titulo del puesto, sector economico y area funcional. Cada clasificacion pasa por un sistema de validacion automatica que detecta inconsistencias, y las ofertas con errores criticos son revisadas manualmente antes de incluirse en el dashboard.",
  },
];

export const metadata = {
  title: "Metodologia | MOL",
  description:
    "Como funciona el Monitor de Ofertas Laborales: fuentes de datos, procesamiento NLP, clasificacion ESCO y validacion.",
};

export default function MetodologiaPage() {
  return (
    <div className="max-w-3xl mx-auto px-4 py-16">
      <span className="inline-block bg-gray-100 text-gray-600 text-[10px] font-bold px-2.5 py-0.5 rounded-full uppercase tracking-wider mb-4">
        Metodologia
      </span>
      <h1 className="text-3xl font-bold text-gray-900 mb-2">
        Como funciona el MOL
      </h1>
      <p className="text-gray-500 mb-10 max-w-2xl">
        El Monitor de Ofertas Laborales procesa miles de ofertas de empleo para
        generar indicadores confiables del mercado laboral argentino.
      </p>

      <div className="space-y-8">
        {sections.map((section, i) => (
          <div key={section.title} className="flex gap-4">
            <div className="shrink-0">
              <div className="w-10 h-10 bg-gray-100 rounded-lg flex items-center justify-center">
                <section.icon className="w-5 h-5 text-gray-600" />
              </div>
            </div>
            <div>
              <h2 className="font-semibold text-gray-900 mb-1">
                <span className="text-gray-400 mr-2">{i + 1}.</span>
                {section.title}
              </h2>
              <p className="text-sm text-gray-500 leading-relaxed">
                {section.content}
              </p>
            </div>
          </div>
        ))}
      </div>

      <div className="mt-12 pt-8 border-t border-gray-200 text-center">
        <Link
          href="/"
          className="text-sm text-gray-400 hover:text-gray-600 transition-colors"
        >
          Volver al inicio
        </Link>
      </div>
    </div>
  );
}

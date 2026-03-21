import Link from "next/link";
import { Search, Lightbulb, ArrowLeftRight, ArrowRight } from "lucide-react";

const cards = [
  {
    title: "Explora ocupaciones",
    description:
      "Descubri las ocupaciones mas demandadas del mercado laboral argentino, con detalle de competencias y requisitos.",
    icon: Search,
    tab: "ocupaciones",
  },
  {
    title: "Descubri tus competencias",
    description:
      "Recorre la taxonomia ESCO de competencias y encontra cuales se alinean con tu perfil profesional.",
    icon: Lightbulb,
    tab: "skills",
  },
  {
    title: "Compara opciones",
    description:
      "Analiza distintas ocupaciones lado a lado para entender las diferencias en competencias y oportunidades.",
    icon: ArrowLeftRight,
    tab: "comparar",
  },
];

export const metadata = {
  title: "Mi Futuro Laboral | MOL",
  description:
    "Explora ocupaciones, descubri competencias y compara opciones para tu carrera profesional.",
};

export default function MiFuturoLaboralPage() {
  return (
    <div className="max-w-4xl mx-auto px-4 py-16">
      <span className="inline-block bg-blue-100 text-blue-700 text-[10px] font-bold px-2.5 py-0.5 rounded-full uppercase tracking-wider mb-4">
        Exploracion Laboral
      </span>
      <h1 className="text-3xl font-bold text-gray-900 mb-2">
        Mi Futuro Laboral
      </h1>
      <p className="text-gray-500 mb-10 max-w-2xl">
        Herramientas para explorar el mercado laboral, descubrir ocupaciones,
        entender que competencias se demandan y planificar tu desarrollo
        profesional.
      </p>

      <div className="grid grid-cols-1 sm:grid-cols-3 gap-6 mb-12">
        {cards.map((card) => (
          <Link
            key={card.tab}
            href={`/skills?tab=${card.tab}`}
            className="group relative bg-white rounded-2xl border-2 border-dashed border-gray-300 p-6 hover:border-blue-400 hover:shadow-lg transition-all"
          >
            <span className="absolute top-3 right-3 bg-blue-100 text-blue-700 text-[10px] font-bold px-2 py-0.5 rounded-full uppercase tracking-wider">
              Disponible
            </span>
            <div className="w-10 h-10 bg-blue-50 rounded-lg flex items-center justify-center mb-4">
              <card.icon className="w-5 h-5 text-blue-600" />
            </div>
            <h3 className="font-semibold text-gray-900 mb-1 text-sm group-hover:text-blue-700 transition-colors">
              {card.title}
            </h3>
            <p className="text-xs text-gray-500 leading-relaxed">
              {card.description}
            </p>
          </Link>
        ))}
      </div>

      <div className="text-center">
        <Link
          href="/skills"
          className="inline-flex items-center gap-2 bg-blue-600 text-white text-sm font-medium px-5 py-2.5 rounded-lg hover:bg-blue-700 transition-colors"
        >
          Explorar Skills
          <ArrowRight className="w-4 h-4" />
        </Link>
      </div>

      <div className="mt-8 text-center">
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

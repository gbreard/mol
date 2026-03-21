import Link from "next/link";
import { UserSearch, Briefcase, Target, ArrowRight } from "lucide-react";

const cards = [
  {
    title: "Perfil Trabajador",
    description:
      "Registra datos, experiencia y competencias de un trabajador para obtener sugerencias personalizadas.",
    icon: UserSearch,
    status: "Proximamente" as const,
  },
  {
    title: "Ofertas Coincidentes",
    description:
      "Consulta las ofertas laborales mas relevantes para un perfil registrado, ordenadas por compatibilidad.",
    icon: Briefcase,
    status: "Proximamente" as const,
  },
  {
    title: "Taxonomia de Skills",
    description:
      "Explora la taxonomia ESCO de competencias y ocupaciones utilizada como referencia internacional.",
    icon: Target,
    status: "Disponible" as const,
  },
];

export const metadata = {
  title: "Oficina de Empleo | MOL",
  description:
    "Herramientas para oficinas de empleo: perfiles de trabajadores, ofertas coincidentes y taxonomia ESCO.",
};

export default function ParaOficinasPage() {
  return (
    <div className="max-w-4xl mx-auto px-4 py-16">
      <span className="inline-block bg-teal-100 text-teal-700 text-[10px] font-bold px-2.5 py-0.5 rounded-full uppercase tracking-wider mb-4">
        Para Oficinas de Empleo
      </span>
      <h1 className="text-3xl font-bold text-gray-900 mb-2">
        Oficina de Empleo
      </h1>
      <p className="text-gray-500 mb-10 max-w-2xl">
        Herramientas para que las oficinas de empleo puedan registrar perfiles de
        trabajadores y encontrar las ofertas laborales mas compatibles con sus
        competencias y experiencia.
      </p>

      <div className="grid grid-cols-1 sm:grid-cols-3 gap-6 mb-12">
        {cards.map((card) => (
          <div
            key={card.title}
            className="relative bg-white rounded-2xl border-2 border-dashed border-gray-300 p-6"
          >
            <span
              className={`absolute top-3 right-3 text-[10px] font-bold px-2 py-0.5 rounded-full uppercase tracking-wider ${
                card.status === "Disponible"
                  ? "bg-teal-100 text-teal-700"
                  : "bg-blue-100 text-blue-700"
              }`}
            >
              {card.status}
            </span>
            <div className="w-10 h-10 bg-teal-50 rounded-lg flex items-center justify-center mb-4">
              <card.icon className="w-5 h-5 text-teal-600" />
            </div>
            <h3 className="font-semibold text-gray-900 mb-1 text-sm">
              {card.title}
            </h3>
            <p className="text-xs text-gray-500 leading-relaxed">
              {card.description}
            </p>
          </div>
        ))}
      </div>

      <div className="bg-teal-50 rounded-2xl p-6 text-center">
        <p className="text-sm text-gray-600 mb-4">
          Para acceder a estas herramientas necesitas una cuenta con rol{" "}
          <span className="font-semibold text-teal-700">
            Oficina de Empleo
          </span>
          .
        </p>
        <Link
          href="/oficina-empleo"
          className="inline-flex items-center gap-2 bg-teal-600 text-white text-sm font-medium px-5 py-2.5 rounded-lg hover:bg-teal-700 transition-colors"
        >
          Acceder
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

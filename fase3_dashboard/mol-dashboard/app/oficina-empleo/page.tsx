import Link from "next/link";
import { UserSearch, Briefcase, Target } from "lucide-react";

const cards = [
  {
    title: "Buscar/Crear Perfil Trabajador",
    description:
      "Registra el perfil de un trabajador con sus datos, experiencia y competencias.",
    href: "/oficina-empleo/perfil",
    icon: UserSearch,
  },
  {
    title: "Ofertas Coincidentes",
    description:
      "Consulta las ofertas laborales mas relevantes para un perfil registrado.",
    href: "/oficina-empleo/ofertas",
    icon: Briefcase,
  },
  {
    title: "Taxonomia de Skills",
    description:
      "Explora la taxonomia ESCO de competencias y ocupaciones.",
    href: "/skills",
    icon: Target,
  },
];

export default function OficinaEmpleoPage() {
  return (
    <div className="max-w-4xl mx-auto px-4 py-16">
      <h1 className="text-3xl font-bold text-gray-900 mb-2">
        Oficina de Empleo
      </h1>
      <p className="text-gray-500 mb-10 max-w-2xl">
        Registra el perfil de un trabajador y el sistema le sugiere skills y
        ofertas adaptadas a su perfil.
      </p>

      <div className="grid grid-cols-1 sm:grid-cols-3 gap-6">
        {cards.map((card) => {
          const isExternal = card.href === "/skills";
          return (
            <Link
              key={card.href}
              href={card.href}
              className="group relative bg-white rounded-2xl border-2 border-dashed border-gray-300 p-6 hover:border-teal-400 hover:shadow-lg transition-all"
            >
              <span className="absolute top-3 right-3 bg-teal-100 text-teal-700 text-[10px] font-bold px-2 py-0.5 rounded-full uppercase tracking-wider">
                {isExternal ? "Disponible" : "Proximamente"}
              </span>
              <div className="w-10 h-10 bg-teal-50 rounded-lg flex items-center justify-center mb-4">
                <card.icon className="w-5 h-5 text-teal-600" />
              </div>
              <h3 className="font-semibold text-gray-900 mb-1 text-sm group-hover:text-teal-700 transition-colors">
                {card.title}
              </h3>
              <p className="text-xs text-gray-500 leading-relaxed">
                {card.description}
              </p>
            </Link>
          );
        })}
      </div>
    </div>
  );
}

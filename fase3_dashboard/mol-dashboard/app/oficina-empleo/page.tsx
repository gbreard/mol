import Link from "next/link";
import { UserSearch, Briefcase, Target, GraduationCap, BarChart3, FileText, Sparkles } from "lucide-react";

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
    title: "Formacion con Impacto",
    description:
      "Cursos que mejoran el match del trabajador con el mercado laboral.",
    href: "/oficina-empleo/formacion",
    icon: GraduationCap,
  },
  {
    title: "Perfil de Puesto",
    description:
      "Crea perfiles de puestos con skills requeridas y deseables.",
    href: "/oficina-empleo/perfil-puesto",
    icon: FileText,
  },
  {
    title: "Benchmark Mercado",
    description:
      "Demanda vs disponibilidad de skills por jurisdiccion.",
    href: "/oficina-empleo/benchmark",
    icon: BarChart3,
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
          return (
            <Link
              key={card.href}
              href={card.href}
              className="group relative bg-white rounded-2xl border-2 border-teal-200 p-6 hover:border-teal-400 hover:shadow-lg transition-all"
            >
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

      {/* S12: Primer ingreso */}
      <div className="mt-8 rounded-xl border border-teal-200 bg-teal-50 p-4 flex flex-col sm:flex-row items-start sm:items-center gap-4">
        <Sparkles className="h-5 w-5 text-teal-600 shrink-0" />
        <div className="flex-1 min-w-0">
          <p className="text-sm font-medium text-teal-900">¿Es tu primer ingreso?</p>
          <p className="text-xs text-teal-700 mt-0.5">Cargá tu planilla de personas para empezar a usar el sistema.</p>
        </div>
        <Link
          href="/oficina-empleo/onboarding"
          className="shrink-0 inline-flex min-h-[44px] items-center gap-2 rounded-lg bg-teal-600 px-4 py-2 text-sm font-medium text-white hover:bg-teal-700"
        >
          Empezar configuración
        </Link>
      </div>
    </div>
  );
}

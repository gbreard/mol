import Link from "next/link";
import { ArrowLeft, CheckCircle2, Zap, Building2, Crown } from "lucide-react";

export default function PreciosPage() {
  const planes = [
    {
      nombre: "Free",
      precio: "Gratis",
      periodo: "",
      descripcion: "Para explorar el mercado laboral",
      icon: Zap,
      color: "blue",
      features: [
        "Dashboard limitado (últimos 7 días)",
        "Solo CABA",
        "Visualizaciones básicas",
      ],
      cta: "Crear cuenta gratuita",
      href: "/registro",
      destacado: false,
    },
    {
      nombre: "Pro",
      precio: "$X",
      periodo: "/mes",
      descripcion: "Para profesionales y consultoras",
      icon: Crown,
      color: "blue",
      features: [
        "Dashboard completo",
        "Histórico completo",
        "Todos los territorios",
        "Exportar Excel/PDF",
        "Alertas por ocupación",
      ],
      cta: "Suscribirse",
      href: "/checkout",
      destacado: true,
    },
    {
      nombre: "Enterprise",
      precio: "$X",
      periodo: "/año",
      descripcion: "Para organizaciones con necesidades avanzadas",
      icon: Building2,
      color: "gray",
      features: [
        "Todo lo de Pro",
        "Acceso a API",
        "Reportes personalizados",
        "Soporte prioritario",
      ],
      cta: "Contactar ventas",
      href: "/registro",
      destacado: false,
    },
  ];

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-50 to-gray-100">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-16">
        <Link
          href="/"
          className="inline-flex items-center gap-2 text-sm text-gray-500 hover:text-blue-600 mb-8 transition-colors"
        >
          <ArrowLeft className="w-4 h-4" />
          Volver al inicio
        </Link>

        <div className="text-center mb-16">
          <h1 className="text-4xl font-bold text-gray-900 mb-4">Planes y precios</h1>
          <p className="text-lg text-gray-500 max-w-2xl mx-auto">
            Elegí el plan que mejor se adapte a tus necesidades de inteligencia laboral
          </p>
        </div>

        <div className="grid md:grid-cols-3 gap-8 max-w-5xl mx-auto">
          {planes.map((plan) => (
            <div
              key={plan.nombre}
              className={`rounded-2xl p-8 ${
                plan.destacado
                  ? "bg-gradient-to-br from-blue-600 to-blue-700 text-white shadow-xl scale-105"
                  : "bg-white border border-gray-200 shadow-lg"
              }`}
            >
              <plan.icon
                className={`w-8 h-8 mb-4 ${plan.destacado ? "text-blue-200" : "text-blue-600"}`}
              />
              <h3
                className={`text-xl font-bold mb-1 ${plan.destacado ? "text-white" : "text-gray-900"}`}
              >
                {plan.nombre}
              </h3>
              <div className="mb-2">
                <span
                  className={`text-3xl font-bold ${plan.destacado ? "text-white" : "text-gray-900"}`}
                >
                  {plan.precio}
                </span>
                <span className={plan.destacado ? "text-blue-200" : "text-gray-400"}>
                  {plan.periodo}
                </span>
              </div>
              <p className={`text-sm mb-6 ${plan.destacado ? "text-blue-100" : "text-gray-500"}`}>
                {plan.descripcion}
              </p>

              <ul className="space-y-3 mb-8">
                {plan.features.map((f) => (
                  <li
                    key={f}
                    className={`flex items-start gap-2 text-sm ${
                      plan.destacado ? "text-blue-50" : "text-gray-600"
                    }`}
                  >
                    <CheckCircle2
                      className={`w-4 h-4 mt-0.5 flex-shrink-0 ${
                        plan.destacado ? "text-blue-200" : "text-green-500"
                      }`}
                    />
                    {f}
                  </li>
                ))}
              </ul>

              <Link
                href={plan.href}
                className={`block w-full text-center text-sm font-semibold px-6 py-3 rounded-xl transition-all ${
                  plan.destacado
                    ? "bg-white text-blue-700 hover:bg-blue-50"
                    : "border border-blue-300 text-blue-600 hover:bg-blue-50"
                }`}
              >
                {plan.cta}
              </Link>
            </div>
          ))}
        </div>

        <p className="text-center text-sm text-gray-400 mt-12">
          Precios provisorios. Sujetos a cambio antes del lanzamiento.
        </p>
      </div>
    </div>
  );
}

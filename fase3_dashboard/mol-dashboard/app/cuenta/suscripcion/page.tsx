import Link from "next/link";
import { createServerClient } from "@/lib/supabase/server";
import { redirect } from "next/navigation";
import {
  getUserProfile,
  isSubscriber,
  PLAN,
  type Plan,
} from "@/lib/user";
import {
  ArrowLeft,
  CheckCircle2,
  Zap,
  Crown,
  Building2,
  ArrowRight,
} from "lucide-react";

const PLAN_CONFIG: Record<
  Plan,
  {
    label: string;
    icon: typeof Zap;
    colorClass: string;
    badgeClass: string;
    features: string[];
  }
> = {
  [PLAN.FREE]: {
    label: "Free",
    icon: Zap,
    colorClass: "bg-gray-50 text-gray-600",
    badgeClass: "bg-gray-100 text-gray-600",
    features: [
      "Dashboard limitado (ultimos 7 dias)",
      "Solo CABA",
      "Visualizaciones basicas",
    ],
  },
  [PLAN.PRO]: {
    label: "Pro",
    icon: Crown,
    colorClass: "bg-green-50 text-green-700",
    badgeClass: "bg-green-100 text-green-700",
    features: [
      "Dashboard completo",
      "Historico completo",
      "Todos los territorios",
      "Exportar Excel/PDF",
      "Alertas por ocupacion",
    ],
  },
  [PLAN.ENTERPRISE]: {
    label: "Enterprise",
    icon: Building2,
    colorClass: "bg-amber-50 text-amber-700",
    badgeClass: "bg-amber-100 text-amber-700",
    features: [
      "Todo lo de Pro",
      "Acceso a API",
      "Reportes personalizados",
      "Soporte prioritario",
    ],
  },
};

export default async function SuscripcionPage() {
  const supabase = await createServerClient();
  const {
    data: { user },
  } = await supabase.auth.getUser();

  if (!user) {
    redirect("/login?next=/cuenta/suscripcion");
  }

  const profile = getUserProfile(user);
  const config = PLAN_CONFIG[profile.plan];
  const subscriber = isSubscriber(profile.plan);
  const PlanIcon = config.icon;

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-50 to-gray-100">
      <div className="max-w-2xl mx-auto px-4 sm:px-6 lg:px-8 py-16">
        <Link
          href="/cuenta"
          className="inline-flex items-center gap-2 text-sm text-gray-500 hover:text-blue-600 mb-8 transition-colors"
        >
          <ArrowLeft className="w-4 h-4" />
          Mi cuenta
        </Link>

        <h1 className="text-3xl font-bold text-gray-900 mb-8">Suscripcion</h1>

        {/* Current plan card */}
        <div className="bg-white rounded-2xl shadow-lg border border-gray-200 p-6 mb-6">
          <div className="flex items-center gap-4 mb-6">
            <div
              className={`w-12 h-12 rounded-xl flex items-center justify-center ${config.colorClass}`}
            >
              <PlanIcon className="w-6 h-6" />
            </div>
            <div>
              <p className="font-bold text-gray-900">Plan actual</p>
              <span
                className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${config.badgeClass}`}
              >
                {config.label}
              </span>
            </div>
          </div>

          {/* Features list */}
          <div className="mb-6">
            <p className="text-sm font-medium text-gray-700 mb-3">
              Tu plan incluye:
            </p>
            <ul className="space-y-2">
              {config.features.map((feature) => (
                <li
                  key={feature}
                  className="flex items-start gap-2 text-sm text-gray-600"
                >
                  <CheckCircle2 className="w-4 h-4 mt-0.5 flex-shrink-0 text-green-500" />
                  {feature}
                </li>
              ))}
            </ul>
          </div>

          {/* CTA */}
          {subscriber ? (
            <div className="bg-green-50 border border-green-200 rounded-xl px-4 py-3">
              <p className="text-sm font-medium text-green-700">
                Plan activo
              </p>
            </div>
          ) : (
            <Link
              href="/precios"
              className="flex items-center justify-center gap-2 w-full bg-gradient-to-r from-blue-600 to-blue-700 text-white font-semibold text-sm px-6 py-3 rounded-xl hover:from-blue-700 hover:to-blue-800 transition-all"
            >
              <Zap className="w-4 h-4" />
              Ver planes
              <ArrowRight className="w-4 h-4" />
            </Link>
          )}
        </div>

        {/* Upgrade banner for free users */}
        {!subscriber && (
          <div className="bg-gradient-to-r from-blue-600 to-blue-700 rounded-2xl shadow-xl p-6 text-center">
            <Crown className="w-8 h-8 text-blue-200 mx-auto mb-3" />
            <h3 className="text-lg font-bold text-white mb-1">
              Desbloquea todo el potencial
            </h3>
            <p className="text-sm text-blue-100 mb-4 max-w-sm mx-auto">
              Dashboard completo, exports, alertas por ocupacion y todos los
              territorios del pais.
            </p>
            <Link
              href="/precios"
              className="inline-flex items-center gap-2 px-5 py-2.5 bg-white text-blue-700 font-semibold rounded-xl hover:bg-blue-50 transition-colors text-sm"
            >
              <Zap className="w-4 h-4" />
              Comparar planes
            </Link>
          </div>
        )}
      </div>
    </div>
  );
}

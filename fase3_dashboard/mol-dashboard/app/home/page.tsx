import Link from "next/link";
import Image from "next/image";
import { redirect } from "next/navigation";
import { createServerClient } from "@/lib/supabase/server";
import {
  getUserProfile,
  getRoleBadge,
  getPlanBadge,
  isAdmin,
  isSubscriber,
  PLAN,
} from "@/lib/user";
import {
  BarChart3,
  Shield,
  FileText,
  Bell,
  Zap,
  Crown,
  LayoutDashboard,
  Settings,
  ArrowRight,
  Calendar,
  User,
} from "lucide-react";
import { LogoutButton } from "./_components/logout-button";

// --- Informes mock (mismo dato que /informes) ---
const informesRecientes = [
  {
    titulo: "Informe trimestral Q4 2025",
    descripcion: "Panorama del mercado laboral argentino: ocupaciones más demandadas, skills emergentes y tendencias territoriales.",
    fecha: "Enero 2026",
  },
  {
    titulo: "Skills digitales en Argentina",
    descripcion: "Estudio especial sobre la demanda de competencias digitales en el mercado laboral argentino.",
    fecha: "Septiembre 2025",
  },
];

export default async function HomePage() {
  const supabase = await createServerClient();
  const { data: { user } } = await supabase.auth.getUser();

  if (!user) {
    redirect("/login");
  }

  const profile = getUserProfile(user);
  const roleBadge = getRoleBadge(profile.role);
  const planBadge = getPlanBadge(profile.plan);
  const admin = isAdmin(profile.role);
  const subscriber = isSubscriber(profile.plan);

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-50 to-gray-100">
      {/* Header */}
      <header className="bg-white border-b border-gray-200">
        <div className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 py-4 flex items-center justify-between">
          <Image src="/logo_mol.png" alt="MOL" width={120} height={40} priority />
          <div className="flex items-center gap-4">
            <Link
              href="/cuenta/suscripcion"
              className="flex items-center gap-2 text-sm text-gray-500 hover:text-gray-700 transition-colors"
            >
              <User className="w-4 h-4" />
              Mi cuenta
            </Link>
            <LogoutButton />
          </div>
        </div>
      </header>

      <main className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 py-10">
        {/* Welcome */}
        <section className="mb-10">
          <h1 className="text-3xl font-bold text-gray-900 mb-2">
            Hola, {profile.displayName}
          </h1>
          <div className="flex items-center gap-2">
            <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${roleBadge.className}`}>
              {roleBadge.label}
            </span>
            {planBadge && (
              <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${planBadge.className}`}>
                {planBadge.label}
              </span>
            )}
          </div>
        </section>

        {/* Quick Access - Admin */}
        {admin && (
          <section className="mb-10">
            <h2 className="text-sm font-semibold text-gray-400 uppercase tracking-wide mb-4">Accesos rápidos</h2>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <Link
                href="/admin"
                className="flex items-center gap-4 bg-white rounded-2xl shadow-lg border border-gray-200 p-6 hover:shadow-xl hover:border-purple-200 transition-all group"
              >
                <div className="w-12 h-12 bg-purple-50 rounded-xl flex items-center justify-center">
                  <Shield className="w-6 h-6 text-purple-600" />
                </div>
                <div className="flex-1">
                  <h3 className="font-bold text-gray-900 group-hover:text-purple-700 transition-colors">Panel Admin</h3>
                  <p className="text-sm text-gray-500">Usuarios, scraping, configuración</p>
                </div>
                <ArrowRight className="w-5 h-5 text-gray-300 group-hover:text-purple-400 transition-colors" />
              </Link>

              <Link
                href="/dashboard"
                className="flex items-center gap-4 bg-white rounded-2xl shadow-lg border border-gray-200 p-6 hover:shadow-xl hover:border-blue-200 transition-all group"
              >
                <div className="w-12 h-12 bg-blue-50 rounded-xl flex items-center justify-center">
                  <BarChart3 className="w-6 h-6 text-blue-600" />
                </div>
                <div className="flex-1">
                  <h3 className="font-bold text-gray-900 group-hover:text-blue-700 transition-colors">Dashboard</h3>
                  <p className="text-sm text-gray-500">Tablero de datos del mercado laboral</p>
                </div>
                <ArrowRight className="w-5 h-5 text-gray-300 group-hover:text-blue-400 transition-colors" />
              </Link>
            </div>
          </section>
        )}

        {/* Quick Access - Subscriber (non-admin) */}
        {!admin && subscriber && (
          <section className="mb-10">
            <h2 className="text-sm font-semibold text-gray-400 uppercase tracking-wide mb-4">Tu tablero</h2>
            <Link
              href="/dashboard"
              className="flex items-center gap-4 bg-gradient-to-r from-blue-600 to-blue-700 rounded-2xl shadow-xl p-6 hover:shadow-2xl transition-all group"
            >
              <div className="w-12 h-12 bg-white/20 rounded-xl flex items-center justify-center">
                <LayoutDashboard className="w-6 h-6 text-white" />
              </div>
              <div className="flex-1">
                <h3 className="font-bold text-white">Ingresar al Dashboard</h3>
                <p className="text-sm text-blue-100">Datos completos del mercado laboral argentino</p>
              </div>
              <ArrowRight className="w-5 h-5 text-blue-200 group-hover:translate-x-1 transition-transform" />
            </Link>

            <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 mt-4">
              <Link
                href="/dashboard/reportes"
                className="flex items-center gap-3 bg-white rounded-xl border border-gray-200 p-4 hover:border-blue-200 hover:shadow-md transition-all"
              >
                <FileText className="w-5 h-5 text-blue-600" />
                <span className="text-sm font-medium text-gray-700">Reportes</span>
              </Link>
              <Link
                href="/dashboard/alertas"
                className="flex items-center gap-3 bg-white rounded-xl border border-gray-200 p-4 hover:border-blue-200 hover:shadow-md transition-all"
              >
                <Bell className="w-5 h-5 text-blue-600" />
                <span className="text-sm font-medium text-gray-700">Alertas</span>
              </Link>
              <Link
                href="/cuenta/suscripcion"
                className="flex items-center gap-3 bg-white rounded-xl border border-gray-200 p-4 hover:border-blue-200 hover:shadow-md transition-all"
              >
                <Settings className="w-5 h-5 text-blue-600" />
                <span className="text-sm font-medium text-gray-700">Mi suscripción</span>
              </Link>
            </div>
          </section>
        )}

        {/* Quick Access - Free user */}
        {!admin && !subscriber && (
          <section className="mb-10">
            <h2 className="text-sm font-semibold text-gray-400 uppercase tracking-wide mb-4">Dashboard</h2>
            <Link
              href="/dashboard"
              className="flex items-center gap-4 bg-white rounded-2xl shadow-lg border border-gray-200 p-6 hover:shadow-xl hover:border-blue-200 transition-all group"
            >
              <div className="w-12 h-12 bg-blue-50 rounded-xl flex items-center justify-center">
                <BarChart3 className="w-6 h-6 text-blue-600" />
              </div>
              <div className="flex-1">
                <h3 className="font-bold text-gray-900 group-hover:text-blue-700 transition-colors">Ingresar al tablero</h3>
                <p className="text-sm text-gray-500">Vista limitada: CABA, últimos 7 días</p>
              </div>
              <ArrowRight className="w-5 h-5 text-gray-300 group-hover:text-blue-400 transition-colors" />
            </Link>
          </section>
        )}

        {/* Informes - visible para todos */}
        <section className="mb-10">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-sm font-semibold text-gray-400 uppercase tracking-wide">Informes</h2>
            <Link
              href="/informes"
              className="text-sm text-blue-600 hover:text-blue-700 font-medium transition-colors"
            >
              Ver todos
            </Link>
          </div>
          <div className="space-y-4">
            {informesRecientes.map((informe) => (
              <div
                key={informe.titulo}
                className="bg-white rounded-xl border border-gray-200 p-5 flex items-start gap-4"
              >
                <div className="w-10 h-10 bg-blue-50 rounded-lg flex items-center justify-center flex-shrink-0">
                  <FileText className="w-5 h-5 text-blue-600" />
                </div>
                <div className="flex-1 min-w-0">
                  <h3 className="font-semibold text-gray-900 text-sm">{informe.titulo}</h3>
                  <p className="text-xs text-gray-500 mt-0.5 line-clamp-1">{informe.descripcion}</p>
                  <span className="inline-flex items-center gap-1 text-xs text-gray-400 mt-2">
                    <Calendar className="w-3 h-3" />
                    {informe.fecha}
                  </span>
                </div>
              </div>
            ))}
          </div>
        </section>

        {/* Upgrade CTA - solo Free */}
        {!admin && !subscriber && (
          <section className="mb-10">
            <div className="bg-gradient-to-r from-blue-600 to-blue-700 rounded-2xl shadow-xl p-8 text-center">
              <div className="flex justify-center mb-4">
                <div className="w-12 h-12 bg-white/20 rounded-xl flex items-center justify-center">
                  <Crown className="w-6 h-6 text-white" />
                </div>
              </div>
              <h3 className="text-xl font-bold text-white mb-2">Desbloqueá todo el potencial</h3>
              <p className="text-sm text-blue-100 mb-6 max-w-md mx-auto">
                Dashboard completo, exports, alertas por ocupación y todos los territorios del país.
              </p>
              <Link
                href="/precios"
                className="inline-flex items-center gap-2 px-6 py-3 bg-white text-blue-700 font-semibold rounded-xl hover:bg-blue-50 transition-colors text-sm"
              >
                <Zap className="w-4 h-4" />
                Ver planes
              </Link>
            </div>
          </section>
        )}

        {/* Account info - subscriber */}
        {!admin && subscriber && (
          <section className="mb-10">
            <div className="bg-white rounded-xl border border-gray-200 p-5 flex items-center justify-between">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 bg-green-50 rounded-lg flex items-center justify-center">
                  <Crown className="w-5 h-5 text-green-600" />
                </div>
                <div>
                  <p className="text-sm font-medium text-gray-900">
                    Plan {profile.plan === PLAN.PRO ? "Pro" : "Enterprise"}
                  </p>
                  <p className="text-xs text-gray-500">Suscripción activa</p>
                </div>
              </div>
              <Link
                href="/cuenta/suscripcion"
                className="text-sm text-blue-600 hover:text-blue-700 font-medium transition-colors"
              >
                Gestionar
              </Link>
            </div>
          </section>
        )}
      </main>
    </div>
  );
}

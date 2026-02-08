import Link from "next/link";
import { createServerClient } from "@/lib/supabase/server";
import { redirect } from "next/navigation";
import {
  getUserProfile,
  getRoleBadge,
  getPlanBadge,
} from "@/lib/user";
import {
  User,
  CreditCard,
  Receipt,
  ChevronRight,
  ArrowLeft,
} from "lucide-react";
import { LogoutButton } from "@/app/home/_components/logout-button";

const secciones = [
  {
    href: "/cuenta/suscripcion",
    icon: CreditCard,
    titulo: "Suscripcion",
    descripcion: "Tu plan actual, upgrade o cancelar",
  },
  {
    href: "#",
    icon: Receipt,
    titulo: "Facturacion",
    descripcion: "Historial de pagos y facturas (proximamente)",
    disabled: true,
  },
] as const;

export default async function CuentaPage() {
  const supabase = await createServerClient();
  const {
    data: { user },
  } = await supabase.auth.getUser();

  if (!user) {
    redirect("/login?next=/cuenta");
  }

  const profile = getUserProfile(user);
  const roleBadge = getRoleBadge(profile.role);
  const planBadge = getPlanBadge(profile.plan);

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-50 to-gray-100">
      <div className="max-w-2xl mx-auto px-4 sm:px-6 lg:px-8 py-16">
        <Link
          href="/home"
          className="inline-flex items-center gap-2 text-sm text-gray-500 hover:text-blue-600 mb-8 transition-colors"
        >
          <ArrowLeft className="w-4 h-4" />
          Volver al inicio
        </Link>

        <h1 className="text-3xl font-bold text-gray-900 mb-8">Mi cuenta</h1>

        {/* Profile card */}
        <div className="bg-white rounded-2xl shadow-lg border border-gray-200 p-6 mb-6">
          <div className="flex items-center gap-4">
            <div className="w-14 h-14 bg-blue-50 rounded-full flex items-center justify-center">
              <User className="w-7 h-7 text-blue-600" />
            </div>
            <div>
              <p className="font-bold text-gray-900">{profile.displayName}</p>
              <p className="text-sm text-gray-500">{profile.email}</p>
              <div className="flex items-center gap-2 mt-1">
                <span
                  className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${roleBadge.className}`}
                >
                  {roleBadge.label}
                </span>
                {planBadge && (
                  <span
                    className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${planBadge.className}`}
                  >
                    {planBadge.label}
                  </span>
                )}
              </div>
            </div>
          </div>
        </div>

        {/* Section links */}
        <div className="space-y-3">
          {secciones.map((sec) => {
            const content = (
              <>
                <div className="w-10 h-10 bg-blue-50 rounded-xl flex items-center justify-center flex-shrink-0">
                  <sec.icon className="w-5 h-5 text-blue-600" />
                </div>
                <div className="flex-1">
                  <p className="font-semibold text-gray-900">{sec.titulo}</p>
                  <p className="text-sm text-gray-500">{sec.descripcion}</p>
                </div>
                <ChevronRight className="w-5 h-5 text-gray-300 group-hover:text-blue-500 transition-colors" />
              </>
            );

            if (sec.disabled) {
              return (
                <div
                  key={sec.titulo}
                  className="flex items-center gap-4 bg-white rounded-2xl shadow-lg border border-gray-200 p-5 opacity-50 cursor-not-allowed"
                >
                  {content}
                </div>
              );
            }

            return (
              <Link
                key={sec.titulo}
                href={sec.href}
                className="flex items-center gap-4 bg-white rounded-2xl shadow-lg border border-gray-200 p-5 hover:border-blue-300 transition-colors group"
              >
                {content}
              </Link>
            );
          })}
        </div>

        {/* Logout */}
        <div className="mt-8 flex items-center justify-between">
          <Link
            href="/home"
            className="text-sm text-gray-500 hover:text-blue-600 transition-colors"
          >
            ← Volver al inicio
          </Link>
          <LogoutButton />
        </div>
      </div>
    </div>
  );
}

import { redirect } from "next/navigation";
import { createServerClient } from "@/lib/supabase/server";
import { getUserProfile, canAccessDashboard } from "@/lib/user";
import { SolicitarAccesoForm } from "./_components/solicitar-acceso-form";

export default async function SolicitarAccesoPage() {
  const supabase = await createServerClient();
  const {
    data: { user },
  } = await supabase.auth.getUser();

  if (!user) {
    redirect("/login?next=/solicitar-acceso");
  }

  const profile = getUserProfile(user);

  // If user already has dashboard access, redirect there
  if (canAccessDashboard(profile.role, profile.plan, profile.trialStartDate)) {
    redirect("/dashboard");
  }

  // Check if user already has a pending solicitud
  const { data: pendingSolicitud } = await supabase
    .from("solicitudes_acceso")
    .select("id, created_at")
    .eq("user_id", user.id)
    .eq("estado", "pendiente")
    .maybeSingle();

  return (
    <div className="max-w-xl mx-auto px-4 py-16">
      <h1 className="text-2xl font-bold text-gray-900 mb-2">
        Solicitar acceso al tablero
      </h1>
      <p className="text-gray-500 mb-8">
        Completa el formulario para solicitar un periodo de prueba de 7 dias.
        Un administrador revisara tu solicitud.
      </p>

      {pendingSolicitud ? (
        <div className="bg-blue-50 border border-blue-200 rounded-xl p-6">
          <h2 className="font-semibold text-blue-800 mb-2">
            Tu solicitud esta pendiente
          </h2>
          <p className="text-sm text-blue-700">
            Enviaste una solicitud el{" "}
            {new Date(pendingSolicitud.created_at).toLocaleDateString("es-AR")}.
            Un administrador la revisara pronto.
          </p>
        </div>
      ) : (
        <SolicitarAccesoForm
          email={profile.email}
          displayName={profile.displayName}
        />
      )}
    </div>
  );
}

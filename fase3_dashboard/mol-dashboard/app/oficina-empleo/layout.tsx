import { redirect } from "next/navigation";
import { createServerClient } from "@/lib/supabase/server";
import { getUserProfile, isAdmin, isOficinaEmpleo } from "@/lib/user";
import { GlobalNav } from "@/components/navigation/GlobalNav";

export default async function OficinaEmpleoLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const supabase = await createServerClient();
  const {
    data: { user },
  } = await supabase.auth.getUser();

  // TODO: restaurar auth check cuando se implemente login real
  // Por ahora S2 está en desarrollo sin flujo de auth
  if (user) {
    const profile = getUserProfile(user);
    if (!isAdmin(profile.role) && !isOficinaEmpleo(profile.role) && profile.role !== 'visit_vip') {
      redirect("/home");
    }
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-50 to-gray-100 flex flex-col">
      <GlobalNav />
      <main className="flex-1">{children}</main>
    </div>
  );
}

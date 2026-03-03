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

  if (!user) {
    redirect("/login?next=/oficina-empleo");
  }

  const profile = getUserProfile(user);
  if (!isAdmin(profile.role) && !isOficinaEmpleo(profile.role)) {
    redirect("/home");
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-50 to-gray-100 flex flex-col">
      <GlobalNav />
      <main className="flex-1">{children}</main>
    </div>
  );
}

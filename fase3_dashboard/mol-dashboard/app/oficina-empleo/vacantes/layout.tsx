import { redirect } from "next/navigation";
import { createServerClient } from "@/lib/supabase/server";
import { getUserProfile } from "@/lib/user";

export default async function VacantesLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  try {
    const supabase = await createServerClient();
    const { data: { user } } = await supabase.auth.getUser();

    if (user) {
      const profile = getUserProfile(user);
      if (profile.role === 'visit_vip') {
        redirect("/vip");
      }
    }
  } catch {}

  return <>{children}</>;
}

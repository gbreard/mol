import { redirect } from "next/navigation";
import { createServerClient } from "@/lib/supabase/server";
import { QueryProvider } from "@/lib/query-provider";
import { GlobalNav } from "@/components/navigation/GlobalNav";
import { getUserProfile, canAccessDashboard } from "@/lib/user";

export default async function DashboardLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const supabase = await createServerClient();
  const { data: { user } } = await supabase.auth.getUser();

  if (!user) {
    redirect("/login?next=/dashboard");
  }

  // Defense-in-depth: middleware already checks, but verify here too
  const profile = getUserProfile(user);
  if (!canAccessDashboard(profile.role, profile.plan, profile.trialStartDate)) {
    redirect("/home?no_access=1");
  }

  return (
    <div className="h-screen flex flex-col overflow-hidden">
      <GlobalNav />
      <div className="flex-1 min-h-0">
        <QueryProvider>{children}</QueryProvider>
      </div>
    </div>
  );
}

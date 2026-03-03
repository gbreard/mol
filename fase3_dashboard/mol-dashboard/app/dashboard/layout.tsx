import { redirect } from "next/navigation";
import { createServerClient } from "@/lib/supabase/server";
import { QueryProvider } from "@/lib/query-provider";
import { GlobalNav } from "@/components/navigation/GlobalNav";

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

  return (
    <div className="h-screen flex flex-col overflow-hidden">
      <GlobalNav />
      <div className="flex-1 min-h-0">
        <QueryProvider>{children}</QueryProvider>
      </div>
    </div>
  );
}

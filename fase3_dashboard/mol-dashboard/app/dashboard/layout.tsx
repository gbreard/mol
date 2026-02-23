import { redirect } from "next/navigation";
import { createServerClient } from "@/lib/supabase/server";
import { QueryProvider } from "@/lib/query-provider";

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

  return <QueryProvider>{children}</QueryProvider>;
}

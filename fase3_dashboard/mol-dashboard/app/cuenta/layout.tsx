import { redirect } from "next/navigation";
import { createServerClient } from "@/lib/supabase/server";

export default async function CuentaLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const supabase = await createServerClient();
  const {
    data: { user },
  } = await supabase.auth.getUser();

  if (!user) {
    redirect("/login?next=/cuenta");
  }

  return <>{children}</>;
}

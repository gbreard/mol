import { redirect } from "next/navigation";
import { createServerClient } from "@/lib/supabase/server";
import { GlobalNav } from "@/components/navigation/GlobalNav";

export default async function ContenidoLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const supabase = await createServerClient();
  const {
    data: { user },
  } = await supabase.auth.getUser();

  if (!user) {
    redirect("/login?next=/contenido");
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-50 to-gray-100 flex flex-col">
      <GlobalNav />
      <main className="flex-1">{children}</main>
    </div>
  );
}

import { redirect } from "next/navigation";

// Admin home redirige al Centro de Control (toda la info está ahí)
export default function AdminPage() {
  redirect("/admin/metricas");
}

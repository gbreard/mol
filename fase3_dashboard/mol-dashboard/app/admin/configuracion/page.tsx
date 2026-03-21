import { redirect } from "next/navigation";

// Configuracion se consolidó en Centro de Control (/admin/metricas)
export default function ConfiguracionPage() {
  redirect("/admin/metricas");
}

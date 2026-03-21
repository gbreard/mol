import Link from "next/link";
import { FileText } from "lucide-react";

export const metadata = {
  title: "Terminos de Uso | MOL",
  description: "Terminos y condiciones de uso del Monitor de Ofertas Laborales.",
};

export default function TerminosPage() {
  return (
    <div className="max-w-3xl mx-auto px-4 py-16">
      <div className="w-12 h-12 bg-gray-100 rounded-xl flex items-center justify-center mb-6">
        <FileText className="w-6 h-6 text-gray-500" />
      </div>
      <h1 className="text-2xl font-bold text-gray-900 mb-2">
        Terminos de Uso
      </h1>
      <span className="inline-block bg-amber-100 text-amber-700 text-[10px] font-bold px-2.5 py-0.5 rounded-full uppercase tracking-wider mb-6">
        En elaboracion
      </span>
      <div className="prose prose-gray prose-sm max-w-none">
        <p className="text-gray-500">
          Los terminos y condiciones de uso del Monitor de Ofertas Laborales
          (MOL) estan siendo elaborados. Este documento detallara las
          condiciones de acceso, uso de datos y responsabilidades de los
          usuarios de la plataforma.
        </p>
        <p className="text-gray-500">
          El MOL es un proyecto del Observatorio de Empleo y Dinamica
          Empresarial (OEDE) del Ministerio de Trabajo, Empleo y Seguridad
          Social de la Republica Argentina.
        </p>
      </div>

      <div className="mt-12 pt-8 border-t border-gray-200 text-center">
        <Link
          href="/"
          className="text-sm text-gray-400 hover:text-gray-600 transition-colors"
        >
          Volver al inicio
        </Link>
      </div>
    </div>
  );
}

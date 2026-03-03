import Link from "next/link";
import { BookOpen, ArrowRight } from "lucide-react";

export default function ContenidoPage() {
  return (
    <div className="max-w-2xl mx-auto px-4 py-24 text-center">
      <div className="w-16 h-16 bg-blue-50 rounded-2xl flex items-center justify-center mx-auto mb-6">
        <BookOpen className="w-8 h-8 text-blue-500" />
      </div>
      <h1 className="text-2xl font-bold text-gray-900 mb-2">Contenido</h1>
      <span className="inline-block bg-blue-100 text-blue-700 text-[10px] font-bold px-2.5 py-0.5 rounded-full uppercase tracking-wider mb-4">
        Proximamente
      </span>
      <p className="text-gray-500 mb-8 max-w-md mx-auto">
        Aca vas a encontrar informes, notas y analisis sobre el mercado
        laboral argentino. Estamos preparando el contenido.
      </p>
      <Link
        href="/informes"
        className="inline-flex items-center gap-2 text-sm text-blue-600 hover:text-blue-700 font-medium transition-colors"
      >
        Mientras tanto, consulta los informes disponibles
        <ArrowRight className="w-4 h-4" />
      </Link>
    </div>
  );
}

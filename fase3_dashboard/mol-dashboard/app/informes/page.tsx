import Link from "next/link";
import { ArrowLeft, FileText, Download, Calendar } from "lucide-react";

export default function InformesPage() {
  const informes = [
    {
      titulo: "Informe trimestral Q4 2025",
      descripcion: "Panorama del mercado laboral argentino: ocupaciones más demandadas, skills emergentes y tendencias territoriales.",
      fecha: "Enero 2026",
    },
    {
      titulo: "Informe trimestral Q3 2025",
      descripcion: "Análisis de la demanda laboral del tercer trimestre con foco en sector tecnología y servicios.",
      fecha: "Octubre 2025",
    },
    {
      titulo: "Skills digitales en Argentina",
      descripcion: "Estudio especial sobre la demanda de competencias digitales en el mercado laboral argentino.",
      fecha: "Septiembre 2025",
    },
  ];

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-50 to-gray-100">
      <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-16">
        <Link
          href="/"
          className="inline-flex items-center gap-2 text-sm text-gray-500 hover:text-blue-600 mb-8 transition-colors"
        >
          <ArrowLeft className="w-4 h-4" />
          Volver al inicio
        </Link>

        <div className="mb-12">
          <h1 className="text-4xl font-bold text-gray-900 mb-4">Informes públicos</h1>
          <p className="text-lg text-gray-500">
            Informes periódicos gratuitos sobre el mercado laboral argentino
          </p>
        </div>

        <div className="space-y-6">
          {informes.map((informe) => (
            <div
              key={informe.titulo}
              className="bg-white rounded-2xl shadow-lg border border-gray-200 p-6 flex items-start gap-6"
            >
              <div className="w-12 h-12 bg-blue-50 rounded-xl flex items-center justify-center flex-shrink-0">
                <FileText className="w-6 h-6 text-blue-600" />
              </div>
              <div className="flex-1">
                <h3 className="text-lg font-bold text-gray-900 mb-1">{informe.titulo}</h3>
                <p className="text-sm text-gray-500 mb-3">{informe.descripcion}</p>
                <div className="flex items-center gap-4">
                  <span className="inline-flex items-center gap-1.5 text-xs text-gray-400">
                    <Calendar className="w-3.5 h-3.5" />
                    {informe.fecha}
                  </span>
                  <button
                    disabled
                    className="inline-flex items-center gap-1.5 text-xs font-medium text-blue-600 opacity-50 cursor-not-allowed"
                  >
                    <Download className="w-3.5 h-3.5" />
                    Próximamente
                  </button>
                </div>
              </div>
            </div>
          ))}
        </div>

        <div className="mt-12 bg-blue-50 border border-blue-100 rounded-2xl p-6 text-center">
          <p className="text-sm text-blue-700">
            Los informes se publicarán periódicamente a medida que el sistema acumule datos históricos.
          </p>
        </div>
      </div>
    </div>
  );
}

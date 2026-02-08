import Link from "next/link";
import { ArrowLeft, Receipt, Construction } from "lucide-react";

export default function FacturacionPage() {
  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-50 to-gray-100">
      <div className="max-w-2xl mx-auto px-4 sm:px-6 lg:px-8 py-16">
        <Link
          href="/cuenta"
          className="inline-flex items-center gap-2 text-sm text-gray-500 hover:text-blue-600 mb-8 transition-colors"
        >
          <ArrowLeft className="w-4 h-4" />
          Mi cuenta
        </Link>

        <h1 className="text-3xl font-bold text-gray-900 mb-2">Facturación</h1>

        <div className="inline-flex items-center gap-2 bg-amber-50 text-amber-700 border border-amber-200 px-4 py-2 rounded-lg text-sm font-medium mb-8">
          <Construction className="w-4 h-4" />
          En desarrollo
        </div>

        <div className="bg-white rounded-2xl shadow-lg border border-gray-200 p-6 text-center">
          <div className="w-12 h-12 bg-gray-50 rounded-xl flex items-center justify-center mx-auto mb-4">
            <Receipt className="w-6 h-6 text-gray-400" />
          </div>
          <p className="text-gray-500 text-sm">
            Acá vas a poder ver tu historial de pagos, descargar facturas y actualizar tus datos de facturación.
          </p>
        </div>
      </div>
    </div>
  );
}

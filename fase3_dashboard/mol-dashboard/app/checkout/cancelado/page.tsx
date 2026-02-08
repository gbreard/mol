import Link from "next/link";
import { XCircle, ArrowLeft } from "lucide-react";

export default function CheckoutCanceladoPage() {
  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-gray-50 to-gray-100">
      <div className="max-w-md w-full mx-4">
        <div className="bg-white rounded-2xl shadow-xl border border-gray-200 p-8 text-center">
          <div className="w-16 h-16 bg-red-50 rounded-2xl flex items-center justify-center mx-auto mb-6">
            <XCircle className="w-8 h-8 text-red-500" />
          </div>

          <h1 className="text-2xl font-bold text-gray-900 mb-2">Pago cancelado</h1>
          <p className="text-gray-500 mb-8">
            El proceso de pago fue cancelado. No se realizó ningún cargo. Podés intentar de nuevo cuando quieras.
          </p>

          <div className="space-y-3">
            <Link
              href="/precios"
              className="block w-full py-3 px-4 bg-gradient-to-r from-blue-600 to-blue-700 text-white rounded-lg text-sm font-semibold hover:from-blue-700 hover:to-blue-800 transition-all shadow-lg"
            >
              Ver planes
            </Link>
            <Link
              href="/"
              className="inline-flex items-center justify-center gap-2 w-full py-3 text-sm text-gray-500 hover:text-blue-600 transition-colors"
            >
              <ArrowLeft className="w-4 h-4" />
              Volver al inicio
            </Link>
          </div>
        </div>
      </div>
    </div>
  );
}

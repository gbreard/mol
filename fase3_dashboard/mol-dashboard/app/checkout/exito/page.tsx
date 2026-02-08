import Link from "next/link";
import { CheckCircle2 } from "lucide-react";

export default function CheckoutExitoPage() {
  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-gray-50 to-gray-100">
      <div className="max-w-md w-full mx-4">
        <div className="bg-white rounded-2xl shadow-xl border border-gray-200 p-8 text-center">
          <div className="w-16 h-16 bg-green-50 rounded-2xl flex items-center justify-center mx-auto mb-6">
            <CheckCircle2 className="w-8 h-8 text-green-500" />
          </div>

          <h1 className="text-2xl font-bold text-gray-900 mb-2">Pago exitoso</h1>
          <p className="text-gray-500 mb-8">
            Tu suscripción fue activada correctamente. Ya podés acceder al dashboard completo.
          </p>

          <Link
            href="/home"
            className="block w-full py-3 px-4 bg-gradient-to-r from-blue-600 to-blue-700 text-white rounded-lg text-sm font-semibold hover:from-blue-700 hover:to-blue-800 transition-all shadow-lg"
          >
            Ir al Dashboard
          </Link>
        </div>
      </div>
    </div>
  );
}

import Link from "next/link";
import { ArrowLeft, CreditCard, Construction } from "lucide-react";

export default function CheckoutPage() {
  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-gray-50 to-gray-100">
      <div className="max-w-lg w-full mx-4">
        <div className="bg-white rounded-2xl shadow-xl border border-gray-200 p-8 text-center">
          <div className="w-16 h-16 bg-blue-50 rounded-2xl flex items-center justify-center mx-auto mb-6">
            <CreditCard className="w-8 h-8 text-blue-600" />
          </div>

          <h1 className="text-2xl font-bold text-gray-900 mb-2">Checkout</h1>

          <div className="inline-flex items-center gap-2 bg-amber-50 text-amber-700 border border-amber-200 px-4 py-2 rounded-lg text-sm font-medium mb-6">
            <Construction className="w-4 h-4" />
            Integración con MercadoPago en desarrollo
          </div>

          <p className="text-gray-500 mb-8">
            Acá vas a poder seleccionar tu plan y completar el pago de forma segura con MercadoPago.
          </p>

          <Link
            href="/precios"
            className="inline-flex items-center gap-2 text-sm text-gray-500 hover:text-blue-600 transition-colors"
          >
            <ArrowLeft className="w-4 h-4" />
            Volver a precios
          </Link>
        </div>
      </div>
    </div>
  );
}

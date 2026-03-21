import Link from "next/link";
import { Shield } from "lucide-react";

export const metadata = {
  title: "Politica de Datos | MOL",
  description:
    "Politica de proteccion de datos personales del Monitor de Ofertas Laborales.",
};

export default function PoliticaDatosPage() {
  return (
    <div className="max-w-3xl mx-auto px-4 py-16">
      <div className="w-12 h-12 bg-gray-100 rounded-xl flex items-center justify-center mb-6">
        <Shield className="w-6 h-6 text-gray-500" />
      </div>
      <h1 className="text-2xl font-bold text-gray-900 mb-2">
        Politica de Datos
      </h1>
      <span className="inline-block bg-amber-100 text-amber-700 text-[10px] font-bold px-2.5 py-0.5 rounded-full uppercase tracking-wider mb-6">
        En elaboracion
      </span>
      <div className="prose prose-gray prose-sm max-w-none">
        <p className="text-gray-500">
          La politica de proteccion de datos personales del Monitor de Ofertas
          Laborales (MOL) esta siendo elaborada. Este documento detallara como
          se recopilan, almacenan, procesan y protegen los datos personales de
          los usuarios.
        </p>
        <p className="text-gray-500">
          El MOL procesa datos publicos de ofertas laborales publicadas en
          portales de empleo. Los datos personales de los usuarios registrados
          (email, nombre, preferencias) se gestionan a traves de Supabase con
          autenticacion segura y control de acceso basado en roles.
        </p>
        <p className="text-gray-500">
          Toda la informacion se maneja conforme a la Ley 25.326 de Proteccion
          de Datos Personales de la Republica Argentina.
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

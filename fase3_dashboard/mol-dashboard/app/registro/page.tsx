"use client";

import { useState, useMemo } from "react";
import { useRouter } from "next/navigation";
import { createBrowserClient } from "@/lib/supabase/browser";
import Image from "next/image";
import Link from "next/link";
import { ArrowLeft, CheckCircle2 } from "lucide-react";

export default function RegistroPage() {
  const [nombre, setNombre] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState(false);
  const router = useRouter();

  const supabase = useMemo(() => {
    if (typeof window === "undefined") return null;
    return createBrowserClient();
  }, []);

  const handleRegistro = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!supabase) {
      setError("Sistema no disponible. Recarga la página.");
      return;
    }

    if (password.length < 6) {
      setError("La contraseña debe tener al menos 6 caracteres");
      return;
    }

    setLoading(true);
    setError(null);

    const { error } = await supabase.auth.signUp({
      email,
      password,
      options: {
        data: {
          display_name: nombre,
          role: "viewer",
          plan: "free",
        },
      },
    });

    if (error) {
      const mensajes: Record<string, string> = {
        "User already registered": "Este email ya está registrado",
        "Password should be at least 6 characters":
          "La contraseña debe tener al menos 6 caracteres",
      };
      setError(mensajes[error.message] ?? error.message);
      setLoading(false);
    } else {
      setSuccess(true);
      setLoading(false);
    }
  };

  if (success) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-gray-50 to-gray-100">
        <div className="max-w-md w-full mx-4">
          <div className="bg-white rounded-2xl shadow-xl border border-gray-200 p-8 text-center">
            <div className="flex justify-center mb-6">
              <Image src="/logo_mol.png" alt="MOL Logo" width={180} height={60} priority />
            </div>

            <div className="w-16 h-16 bg-green-50 rounded-2xl flex items-center justify-center mx-auto mb-6">
              <CheckCircle2 className="w-8 h-8 text-green-500" />
            </div>

            <h1 className="text-2xl font-bold text-gray-900 mb-2">Cuenta creada</h1>
            <p className="text-gray-500 mb-8">
              Revisá tu casilla de email para confirmar tu cuenta. Una vez confirmada, podés iniciar sesión.
            </p>

            <Link
              href="/login"
              className="block w-full py-3 px-4 bg-gradient-to-r from-blue-600 to-blue-700 text-white rounded-lg text-sm font-semibold hover:from-blue-700 hover:to-blue-800 transition-all shadow-lg"
            >
              Ir al Login
            </Link>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-gray-50 to-gray-100">
      <div className="max-w-md w-full mx-4">
        <div className="bg-white rounded-2xl shadow-xl border border-gray-200 p-8">
          {/* Logo */}
          <div className="flex justify-center mb-6">
            <Image src="/logo_mol.png" alt="MOL Logo" width={180} height={60} priority />
          </div>

          <h1 className="text-2xl font-bold text-center text-gray-900 mb-2">
            Crear cuenta
          </h1>
          <p className="text-center text-gray-500 mb-8">
            Registrate gratis para acceder al Monitor de Ofertas Laborales
          </p>

          {error && (
            <div className="mb-6 p-4 bg-red-50 border border-red-200 text-red-700 rounded-lg text-sm">
              {error}
            </div>
          )}

          <form onSubmit={handleRegistro} className="space-y-5">
            <div>
              <label htmlFor="nombre" className="block text-sm font-medium text-gray-700 mb-2">
                Nombre
              </label>
              <input
                id="nombre"
                type="text"
                value={nombre}
                onChange={(e) => setNombre(e.target.value)}
                className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 text-sm transition-colors"
                placeholder="Tu nombre"
                required
                disabled={loading}
              />
            </div>

            <div>
              <label htmlFor="email" className="block text-sm font-medium text-gray-700 mb-2">
                Email
              </label>
              <input
                id="email"
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 text-sm transition-colors"
                placeholder="tu@email.com"
                required
                disabled={loading}
              />
            </div>

            <div>
              <label htmlFor="password" className="block text-sm font-medium text-gray-700 mb-2">
                Contraseña
              </label>
              <input
                id="password"
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 text-sm transition-colors"
                placeholder="Mínimo 6 caracteres"
                required
                minLength={6}
                disabled={loading}
              />
            </div>

            <button
              type="submit"
              disabled={loading}
              className="w-full py-3 px-4 bg-gradient-to-r from-blue-600 to-blue-700 text-white rounded-lg text-sm font-semibold hover:from-blue-700 hover:to-blue-800 transition-all shadow-lg hover:shadow-xl disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {loading ? "Creando cuenta..." : "Crear cuenta gratuita"}
            </button>
          </form>

          <div className="mt-6 text-center">
            <span className="text-sm text-gray-500">¿Ya tenés cuenta? </span>
            <Link href="/login" className="text-sm font-semibold text-blue-600 hover:text-blue-700">
              Iniciar sesión
            </Link>
          </div>

          <div className="mt-4">
            <Link
              href="/"
              className="inline-flex items-center justify-center gap-2 w-full py-2 text-sm text-gray-400 hover:text-blue-600 transition-colors"
            >
              <ArrowLeft className="w-4 h-4" />
              Volver al inicio
            </Link>
          </div>

          <p className="mt-6 text-center text-xs text-gray-400">
            OEDE - Observatorio de Empleo y Dinámica Empresarial
          </p>
        </div>
      </div>
    </div>
  );
}

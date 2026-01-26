'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import { createClient } from '@/lib/supabase/browser';
import { User } from '@supabase/supabase-js';

interface Usuario {
  id: string;
  nombre: string;
  email: string;
  rol: 'platform_admin' | 'admin' | 'analista' | 'lector';
  organizacion?: {
    nombre: string;
  };
}

const rolLabels: Record<string, string> = {
  platform_admin: 'SuperAdmin',
  admin: 'Admin',
  analista: 'Analista',
  lector: 'Lector',
};

const rolColors: Record<string, string> = {
  platform_admin: 'bg-purple-100 text-purple-800',
  admin: 'bg-blue-100 text-blue-800',
  analista: 'bg-green-100 text-green-800',
  lector: 'bg-gray-100 text-gray-800',
};

export default function Header() {
  const [user, setUser] = useState<User | null>(null);
  const [usuario, setUsuario] = useState<Usuario | null>(null);
  const [loading, setLoading] = useState(true);
  const [menuOpen, setMenuOpen] = useState(false);

  const supabase = createClient();
  const router = useRouter();

  useEffect(() => {
    const getUser = async () => {
      const { data: { user } } = await supabase.auth.getUser();
      setUser(user);

      if (user) {
        const { data } = await supabase
          .from('usuarios')
          .select('id, nombre, email, rol, organizacion:organizaciones(nombre)')
          .eq('auth_id', user.id)
          .single();

        if (data) {
          setUsuario(data as unknown as Usuario);
        }
      }
      setLoading(false);
    };

    getUser();

    const { data: { subscription } } = supabase.auth.onAuthStateChange(
      (_event, session) => {
        setUser(session?.user ?? null);
        if (!session?.user) {
          setUsuario(null);
        }
      }
    );

    return () => subscription.unsubscribe();
  }, [supabase]);

  const handleLogout = async () => {
    await supabase.auth.signOut();
    router.push('/login');
    router.refresh();
  };

  const getInitials = (nombre: string) => {
    return nombre
      .split(' ')
      .map(n => n[0])
      .slice(0, 2)
      .join('')
      .toUpperCase();
  };

  return (
    <header className="bg-white shadow-sm border-b border-gray-200">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between items-center h-16">
          {/* Logo y titulo */}
          <div className="flex items-center space-x-3">
            <Link href="/" className="flex items-center space-x-3">
              <div className="w-10 h-10 bg-blue-600 rounded-lg flex items-center justify-center">
                <span className="text-white font-bold text-lg">M</span>
              </div>
              <div>
                <h1 className="text-xl font-semibold text-gray-900">MOL</h1>
                <p className="text-xs text-gray-500">Monitor de Ofertas Laborales</p>
              </div>
            </Link>
          </div>

          {/* Usuario y menu */}
          <div className="flex items-center space-x-4">
            {loading ? (
              <div className="animate-pulse flex items-center space-x-2">
                <div className="w-8 h-8 bg-gray-200 rounded-full"></div>
                <div className="w-24 h-4 bg-gray-200 rounded"></div>
              </div>
            ) : usuario ? (
              <>
                {/* Organizacion */}
                {usuario.organizacion && (
                  <span className="text-sm text-gray-500 hidden sm:block">
                    {usuario.organizacion.nombre}
                  </span>
                )}

                {/* Badge de rol */}
                <span className={`px-2 py-1 text-xs font-medium rounded-full ${rolColors[usuario.rol]}`}>
                  {rolLabels[usuario.rol]}
                </span>

                {/* Menu de usuario */}
                <div className="relative">
                  <button
                    onClick={() => setMenuOpen(!menuOpen)}
                    className="flex items-center space-x-2 focus:outline-none"
                  >
                    <div className="w-8 h-8 bg-blue-600 rounded-full flex items-center justify-center">
                      <span className="text-sm font-medium text-white">
                        {getInitials(usuario.nombre)}
                      </span>
                    </div>
                    <span className="text-sm font-medium text-gray-700 hidden sm:block">
                      {usuario.nombre}
                    </span>
                    <svg
                      className={`w-4 h-4 text-gray-400 transition-transform ${menuOpen ? 'rotate-180' : ''}`}
                      fill="none"
                      stroke="currentColor"
                      viewBox="0 0 24 24"
                    >
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                    </svg>
                  </button>

                  {/* Dropdown menu */}
                  {menuOpen && (
                    <div className="absolute right-0 mt-2 w-48 bg-white rounded-md shadow-lg border border-gray-200 py-1 z-50">
                      <div className="px-4 py-2 border-b border-gray-100">
                        <p className="text-sm font-medium text-gray-900">{usuario.nombre}</p>
                        <p className="text-xs text-gray-500">{usuario.email}</p>
                      </div>

                      {/* Links segun rol */}
                      {['platform_admin', 'admin'].includes(usuario.rol) && (
                        <>
                          <Link
                            href="/admin/usuarios"
                            className="block px-4 py-2 text-sm text-gray-700 hover:bg-gray-50"
                            onClick={() => setMenuOpen(false)}
                          >
                            Panel de Admin
                          </Link>
                        </>
                      )}

                      {usuario.rol === 'platform_admin' && (
                        <Link
                          href="/superadmin/metricas"
                          className="block px-4 py-2 text-sm text-gray-700 hover:bg-gray-50"
                          onClick={() => setMenuOpen(false)}
                        >
                          SuperAdmin
                        </Link>
                      )}

                      <button
                        onClick={handleLogout}
                        className="block w-full text-left px-4 py-2 text-sm text-red-600 hover:bg-red-50"
                      >
                        Cerrar sesion
                      </button>
                    </div>
                  )}
                </div>
              </>
            ) : (
              <Link
                href="/login"
                className="text-sm font-medium text-blue-600 hover:text-blue-700"
              >
                Iniciar sesion
              </Link>
            )}
          </div>
        </div>
      </div>

      {/* Click outside to close menu */}
      {menuOpen && (
        <div
          className="fixed inset-0 z-40"
          onClick={() => setMenuOpen(false)}
        />
      )}
    </header>
  );
}

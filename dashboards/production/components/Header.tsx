"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import Image from "next/image";
import { User, LogOut, ChevronDown, Shield } from "lucide-react";
import { createBrowserClient } from "@/lib/supabase/browser";

interface UserInfo {
  email: string;
  role: string;
  displayName: string;
}

export function Header() {
  const router = useRouter();
  const [user, setUser] = useState<UserInfo | null>(null);
  const [showMenu, setShowMenu] = useState(false);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function loadUser() {
      const supabase = createBrowserClient();
      const { data: { user: authUser } } = await supabase.auth.getUser();

      if (authUser) {
        // Obtener rol del user_metadata o default a 'usuario'
        const role = authUser.user_metadata?.role || 'admin';
        const displayName = authUser.user_metadata?.display_name ||
                           authUser.email?.split('@')[0] ||
                           'Usuario';

        setUser({
          email: authUser.email || '',
          role: role,
          displayName: displayName
        });
      }
      setLoading(false);
    }
    loadUser();
  }, []);

  const handleLogout = async () => {
    const supabase = createBrowserClient();
    await supabase.auth.signOut();
    router.push('/login');
  };

  const getRoleLabel = (role: string) => {
    const roles: Record<string, string> = {
      'super_admin': 'Super Admin',
      'admin': 'Administrador',
      'analyst': 'Analista',
      'viewer': 'Visualizador',
      'usuario': 'Usuario'
    };
    return roles[role] || role;
  };

  const getRoleBadgeColor = (role: string) => {
    const colors: Record<string, string> = {
      'super_admin': 'bg-purple-100 text-purple-800',
      'admin': 'bg-blue-100 text-blue-800',
      'analyst': 'bg-green-100 text-green-800',
      'viewer': 'bg-gray-100 text-gray-800',
      'usuario': 'bg-gray-100 text-gray-800'
    };
    return colors[role] || 'bg-gray-100 text-gray-800';
  };

  return (
    <header className="h-20 border-b border-gray-200 bg-gradient-to-r from-white to-gray-50 flex items-center justify-between px-8 shadow-md">
      <div className="flex items-center gap-5">
        <div className="relative w-16 h-16 flex items-center justify-center">
          <Image
            src="/logo_mol2.png"
            alt="Logo MOL"
            width={64}
            height={64}
            className="object-contain"
            priority
          />
        </div>
        <h1 className="text-2xl font-bold text-gray-900 tracking-tight">Monitor de Oferta Laborales</h1>
      </div>

      <div className="flex items-center gap-4">
        {/* Botón Admin - siempre visible cuando hay usuario */}
        {user && (
          <a
            href="/admin"
            className="flex items-center gap-2 bg-purple-600 text-white px-4 py-2 rounded-lg hover:bg-purple-700 transition-colors shadow-sm"
          >
            <Shield className="w-5 h-5" />
            <span className="font-medium">Admin</span>
          </a>
        )}

        <div className="relative">
          <button
            onClick={() => setShowMenu(!showMenu)}
            className="flex items-center gap-3 bg-white border border-gray-200 rounded-lg px-4 py-2 shadow-sm hover:shadow-md transition-shadow cursor-pointer"
          >
          <div className="bg-blue-600 rounded-full p-2">
            <User className="w-5 h-5 text-white" />
          </div>
          <div className="flex flex-col items-start">
            {loading ? (
              <span className="text-sm text-gray-400">Cargando...</span>
            ) : user ? (
              <>
                <span className="text-sm font-semibold text-gray-900">{user.displayName}</span>
                <span className={`text-xs px-2 py-0.5 rounded-full ${getRoleBadgeColor(user.role)}`}>
                  {getRoleLabel(user.role)}
                </span>
              </>
            ) : (
              <span className="text-sm text-gray-500">No autenticado</span>
            )}
          </div>
          <ChevronDown className={`w-4 h-4 text-gray-400 transition-transform ${showMenu ? 'rotate-180' : ''}`} />
        </button>

        {showMenu && user && (
          <div className="absolute right-0 mt-2 w-56 bg-white border border-gray-200 rounded-lg shadow-lg z-50">
            <div className="px-4 py-3 border-b border-gray-100">
              <p className="text-sm font-medium text-gray-900">{user.displayName}</p>
              <p className="text-xs text-gray-500 truncate">{user.email}</p>
            </div>
            <div className="py-1">
              <button
                onClick={() => { setShowMenu(false); router.push('/admin'); }}
                className="w-full flex items-center gap-2 px-4 py-2 text-sm text-purple-600 hover:bg-purple-50 transition-colors"
              >
                <Shield className="w-4 h-4" />
                Panel de Admin
              </button>
              <button
                onClick={handleLogout}
                className="w-full flex items-center gap-2 px-4 py-2 text-sm text-red-600 hover:bg-red-50 transition-colors"
              >
                <LogOut className="w-4 h-4" />
                Cerrar sesión
              </button>
            </div>
          </div>
          )}
        </div>
      </div>

      {/* Overlay para cerrar el menú */}
      {showMenu && (
        <div
          className="fixed inset-0 z-40"
          onClick={() => setShowMenu(false)}
        />
      )}
    </header>
  );
}

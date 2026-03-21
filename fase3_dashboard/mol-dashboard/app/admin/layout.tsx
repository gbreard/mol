"use client";

import { useState, useEffect } from "react";
import { useRouter, usePathname } from "next/navigation";
import Link from "next/link";
import {
  Users,
  UserPlus,
  BarChart3,
  Database,
  FileText,
  Settings,
  Shield,
  ChevronLeft,
  ChevronDown,
  Loader2,
  MessageSquare,
  Target,
  Network,
  FlaskConical,
  ClipboardCheck,
  Activity,
} from "lucide-react";
import { createBrowserClient } from "@/lib/supabase/browser";
import { GlobalNav } from "@/components/navigation/GlobalNav";

interface MenuItem {
  href: string;
  label: string;
  icon: any;
  matchMode?: "startsWith";
}

interface SubMenu {
  label: string;
  icon: any;
  matchPrefix: string;
  items: MenuItem[];
}

interface MenuSection {
  label: string;
  defaultOpen: boolean;
  items: (MenuItem | SubMenu)[];
}

function isSubMenu(item: MenuItem | SubMenu): item is SubMenu {
  return 'items' in item;
}

const adminSections: MenuSection[] = [
  {
    label: "Operaciones",
    defaultOpen: true,
    items: [
      { href: "/admin/metricas", label: "Centro de Control", icon: BarChart3 },
      {
        label: "Scraping",
        icon: Database,
        matchPrefix: "/admin/scraping",
        items: [
          { href: "/admin/scraping", label: "Portales", icon: Database },
        ],
      },
      {
        label: "Procesamiento",
        icon: Activity,
        matchPrefix: "/admin/validacion",
        items: [
          { href: "/admin/validacion", label: "Validacion", icon: ClipboardCheck, matchMode: "startsWith" },
        ],
      },
      { href: "/admin/issues", label: "Issues", icon: MessageSquare },
    ],
  },
  {
    label: "Datos",
    defaultOpen: true,
    items: [
      { href: "/admin/skills", label: "Skills Intelligence", icon: Target },
      { href: "/admin/laboratorio", label: "Laboratorio", icon: FlaskConical, matchMode: "startsWith" },
    ],
  },
  {
    label: "Administracion",
    defaultOpen: false,
    items: [
      { href: "/admin/usuarios", label: "Usuarios", icon: Users },
      { href: "/admin/solicitudes", label: "Solicitudes", icon: UserPlus },
      { href: "/admin/logs", label: "Logs", icon: FileText },
      { href: "/admin/arquitectura", label: "Arquitectura", icon: Network },
    ],
  },
];

function DesktopAdminSidebar({ pathname }: { pathname: string }) {
  const [openSections, setOpenSections] = useState<Record<string, boolean>>(() => {
    const init: Record<string, boolean> = {};
    adminSections.forEach(s => { init[s.label] = s.defaultOpen; });
    return init;
  });

  const [openSubMenus, setOpenSubMenus] = useState<Record<string, boolean>>(() => {
    const init: Record<string, boolean> = {};
    adminSections.forEach(s => {
      s.items.forEach(item => {
        if (isSubMenu(item)) {
          init[item.label] = pathname.startsWith(item.matchPrefix);
        }
      });
    });
    return init;
  });

  const isItemActive = (item: MenuItem) => {
    if (item.matchMode === "startsWith") return pathname.startsWith(item.href) && pathname !== "/admin";
    return pathname === item.href;
  };

  const isSubMenuActive = (sub: SubMenu) => sub.items.some(i => isItemActive(i));

  return (
    <div className="space-y-4">
      {adminSections.map((section) => {
        const sectionOpen = openSections[section.label] ?? true;
        const hasActive = section.items.some(item =>
          isSubMenu(item) ? isSubMenuActive(item) : isItemActive(item)
        );

        return (
          <div key={section.label}>
            <button
              onClick={() => setOpenSections(prev => ({ ...prev, [section.label]: !prev[section.label] }))}
              className="w-full flex items-center justify-between px-3 py-1.5"
            >
              <span className={`text-xs uppercase tracking-wider font-semibold ${
                hasActive ? 'text-purple-400' : 'text-slate-500'
              }`}>
                {section.label}
              </span>
              <ChevronDown className={`w-3.5 h-3.5 text-slate-500 transition-transform ${sectionOpen ? '' : '-rotate-90'}`} />
            </button>

            {sectionOpen && (
              <div className="space-y-0.5 mt-1">
                {section.items.map((item) => {
                  if (isSubMenu(item)) {
                    const subOpen = openSubMenus[item.label] ?? false;
                    const subActive = isSubMenuActive(item);
                    const Icon = item.icon;

                    return (
                      <div key={item.label}>
                        <button
                          onClick={() => setOpenSubMenus(prev => ({ ...prev, [item.label]: !prev[item.label] }))}
                          className={`w-full flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm transition-colors ${
                            subActive ? 'text-purple-300 bg-slate-800' : 'text-slate-300 hover:bg-slate-800 hover:text-white'
                          }`}
                        >
                          <Icon className="w-5 h-5" />
                          <span className="flex-1 text-left">{item.label}</span>
                          <ChevronDown className={`w-3.5 h-3.5 transition-transform ${subOpen ? '' : '-rotate-90'}`} />
                        </button>

                        {subOpen && (
                          <div className="ml-5 pl-3 border-l border-slate-700 space-y-0.5 mt-0.5">
                            {item.items.map((subItem) => {
                              const active = isItemActive(subItem);
                              return (
                                <Link
                                  key={subItem.href}
                                  href={subItem.href}
                                  className={`flex items-center gap-3 px-3 py-2 rounded-lg text-sm transition-colors ${
                                    active ? 'bg-purple-600 text-white' : 'text-slate-400 hover:bg-slate-800 hover:text-white'
                                  }`}
                                >
                                  <subItem.icon className="w-4 h-4" />
                                  {subItem.label}
                                </Link>
                              );
                            })}
                          </div>
                        )}
                      </div>
                    );
                  }

                  const menuItem = item as MenuItem;
                  const active = isItemActive(menuItem);
                  return (
                    <Link
                      key={menuItem.href}
                      href={menuItem.href}
                      className={`flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm transition-colors ${
                        active ? 'bg-purple-600 text-white' : 'text-slate-300 hover:bg-slate-800 hover:text-white'
                      }`}
                    >
                      <menuItem.icon className="w-5 h-5" />
                      {menuItem.label}
                    </Link>
                  );
                })}
              </div>
            )}
          </div>
        );
      })}
    </div>
  );
}

export default function AdminLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const router = useRouter();
  const pathname = usePathname();
  const [loading, setLoading] = useState(true);
  const [authorized, setAuthorized] = useState(false);

  useEffect(() => {
    async function checkAuth() {
      const supabase = createBrowserClient();
      const { data: { user } } = await supabase.auth.getUser();

      if (!user) {
        router.push("/login");
        return;
      }

      // Verificar rol de admin (sin default — sin metadata = sin acceso)
      const role = user.user_metadata?.role;
      if (role !== 'admin' && role !== 'super_admin') {
        router.push("/dashboard");
        return;
      }

      setAuthorized(true);
      setLoading(false);
    }
    checkAuth();
  }, [router]);

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50">
        <Loader2 className="w-8 h-8 animate-spin text-blue-600" />
        <span className="ml-3 text-gray-600">Verificando permisos...</span>
      </div>
    );
  }

  if (!authorized) {
    return null;
  }

  return (
    <div className="min-h-screen bg-gray-50 flex flex-col">
      <GlobalNav />
      <div className="flex flex-1">
        {/* Sidebar — hidden on mobile (GlobalNav Sheet handles it) */}
        <aside className="hidden md:flex w-64 bg-slate-900 text-white flex-col shrink-0">
          <div className="p-5 border-b border-slate-700">
            <div className="flex items-center gap-3">
              <Shield className="w-7 h-7 text-purple-400" />
              <div>
                <h1 className="font-bold text-base">Admin Panel</h1>
                <p className="text-xs text-slate-400">MOL SuperAdmin</p>
              </div>
            </div>
          </div>

          <nav className="flex-1 p-3 overflow-y-auto">
            <DesktopAdminSidebar pathname={pathname} />
          </nav>

          <div className="p-4 border-t border-slate-700">
            <Link
              href="/dashboard"
              className="flex items-center gap-2 text-slate-400 hover:text-white transition-colors text-sm"
            >
              <ChevronLeft className="w-4 h-4" />
              Volver al Dashboard
            </Link>
          </div>
        </aside>

        {/* Main content */}
        <main className="flex-1 overflow-auto">
          {children}
        </main>
      </div>
    </div>
  );
}

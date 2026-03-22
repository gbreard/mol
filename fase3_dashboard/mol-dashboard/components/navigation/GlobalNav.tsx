"use client";

import { useState, useEffect } from "react";
import { useRouter, usePathname } from "next/navigation";
import Link from "next/link";
import Image from "next/image";
import {
  Home,
  BarChart3,
  Shield,
  Target,
  User,
  LogOut,
  ChevronDown,
  Menu,
  Users,
  UserPlus,
  Database,
  FileText,
  Settings,
  MessageSquare,
  Network,
  FlaskConical,
  ClipboardCheck,
  BookOpen,
  Briefcase,
} from "lucide-react";
import { createBrowserClient } from "@/lib/supabase/browser";
import {
  Sheet,
  SheetContent,
  SheetHeader,
  SheetTitle,
} from "@/components/ui/sheet";

/* ─── Types ───────────────────────────────────────────── */

interface UserInfo {
  email: string;
  role: string;
  plan: string;
  displayName: string;
}

interface NavItem {
  label: string;
  href: string;
  icon: React.ComponentType<{ className?: string }>;
  roles: "*" | string[];
  plans?: string[];
  matchMode?: "exact" | "startsWith";
}

/* ─── Config ──────────────────────────────────────────── */

const NAV_ITEMS: NavItem[] = [
  { label: "Inicio", href: "/", icon: Home, roles: "*", matchMode: "exact" },
  {
    label: "Dashboard",
    href: "/dashboard",
    icon: BarChart3,
    roles: ["super_admin", "admin", "analyst", "viewer"],
    plans: ["pro", "enterprise", "trial"],
    matchMode: "startsWith",
  },
  {
    label: "Contenido",
    href: "/contenido",
    icon: BookOpen,
    roles: ["super_admin", "admin", "analyst", "viewer", "oficina_empleo"],
    matchMode: "startsWith",
  },
  {
    label: "Skills",
    href: "/skills",
    icon: Target,
    roles: ["super_admin", "admin", "oficina_empleo"],
    matchMode: "startsWith",
  },
  {
    label: "Oficina de Empleo",
    href: "/oficina-empleo",
    icon: Briefcase,
    roles: ["super_admin", "admin", "oficina_empleo"],
    matchMode: "startsWith",
  },
  {
    label: "Mi Futuro Laboral",
    href: "/mi-futuro-laboral",
    icon: Target,
    roles: "*",
    matchMode: "startsWith",
  },
  {
    label: "Informes",
    href: "/informes",
    icon: FileText,
    roles: "*",
    matchMode: "startsWith",
  },
  {
    label: "Admin",
    href: "/admin",
    icon: Shield,
    roles: ["super_admin", "admin"],
    matchMode: "startsWith",
  },
];

interface AdminMenuItem {
  href: string;
  label: string;
  icon: any;
  matchMode?: "exact" | "startsWith";
}

interface AdminSubMenu {
  label: string;
  icon: any;
  matchPrefix: string; // para detectar si el submenu tiene un item activo
  items: AdminMenuItem[];
}

interface AdminSidebarSection {
  label: string;
  defaultOpen?: boolean;
  items: (AdminMenuItem | AdminSubMenu)[];
}

function isSubMenu(item: AdminMenuItem | AdminSubMenu): item is AdminSubMenu {
  return 'items' in item && Array.isArray((item as any).items);
}

const ADMIN_SIDEBAR_SECTIONS: AdminSidebarSection[] = [
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
          { href: "/admin/scraping/comandos", label: "Comandos", icon: Settings, matchMode: "startsWith" },
        ],
      },
      {
        label: "Procesamiento",
        icon: Settings,
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

// Flat list for backward compat
const ADMIN_SIDEBAR_ITEMS = ADMIN_SIDEBAR_SECTIONS.flatMap(s =>
  s.items.flatMap(item => isSubMenu(item) ? item.items : [item])
);

/* ─── Admin Sidebar Component ─────────────────────────── */

function AdminSidebar({ pathname, onNavigate }: { pathname: string; onNavigate: () => void }) {
  // Track which sections and submenus are open
  const [openSections, setOpenSections] = useState<Record<string, boolean>>(() => {
    const initial: Record<string, boolean> = {};
    ADMIN_SIDEBAR_SECTIONS.forEach(s => {
      initial[s.label] = s.defaultOpen ?? true;
    });
    return initial;
  });

  const [openSubMenus, setOpenSubMenus] = useState<Record<string, boolean>>(() => {
    // Auto-open submenu if current path matches
    const initial: Record<string, boolean> = {};
    ADMIN_SIDEBAR_SECTIONS.forEach(s => {
      s.items.forEach(item => {
        if (isSubMenu(item)) {
          initial[item.label] = pathname.startsWith(item.matchPrefix);
        }
      });
    });
    return initial;
  });

  const toggleSection = (label: string) => {
    setOpenSections(prev => ({ ...prev, [label]: !prev[label] }));
  };

  const toggleSubMenu = (label: string) => {
    setOpenSubMenus(prev => ({ ...prev, [label]: !prev[label] }));
  };

  const isItemActive = (item: AdminMenuItem) => {
    if (item.matchMode === "startsWith") {
      return pathname.startsWith(item.href) && pathname !== "/admin";
    }
    return pathname === item.href;
  };

  const isSubMenuActive = (sub: AdminSubMenu) => {
    return sub.items.some(item => isItemActive(item));
  };

  return (
    <div className="space-y-3">
      {ADMIN_SIDEBAR_SECTIONS.map((section) => {
        const sectionOpen = openSections[section.label] ?? true;
        const hasSectionActive = section.items.some(item =>
          isSubMenu(item) ? isSubMenuActive(item) : isItemActive(item)
        );

        return (
          <div key={section.label}>
            {/* Section header (collapsible) */}
            <button
              onClick={() => toggleSection(section.label)}
              className="w-full flex items-center justify-between px-3 py-1.5 group"
            >
              <span className={`text-xs uppercase tracking-wider font-semibold ${
                hasSectionActive ? 'text-purple-400' : 'text-slate-500'
              }`}>
                {section.label}
              </span>
              <ChevronDown className={`w-3 h-3 text-slate-500 transition-transform ${
                sectionOpen ? '' : '-rotate-90'
              }`} />
            </button>

            {/* Section items */}
            {sectionOpen && (
              <div className="space-y-0.5 mt-0.5">
                {section.items.map((item) => {
                  if (isSubMenu(item)) {
                    const subOpen = openSubMenus[item.label] ?? false;
                    const subActive = isSubMenuActive(item);
                    const Icon = item.icon;

                    return (
                      <div key={item.label}>
                        {/* Submenu toggle */}
                        <button
                          onClick={() => toggleSubMenu(item.label)}
                          className={`w-full flex items-center gap-3 px-3 py-2 rounded-lg text-sm transition-colors ${
                            subActive
                              ? 'text-purple-300 bg-slate-800'
                              : 'text-slate-400 hover:bg-slate-800 hover:text-white'
                          }`}
                        >
                          <Icon className="w-4 h-4" />
                          <span className="flex-1 text-left">{item.label}</span>
                          <ChevronDown className={`w-3 h-3 transition-transform ${
                            subOpen ? '' : '-rotate-90'
                          }`} />
                        </button>

                        {/* Submenu items */}
                        {subOpen && (
                          <div className="ml-4 pl-3 border-l border-slate-700 space-y-0.5 mt-0.5">
                            {item.items.map((subItem) => {
                              const active = isItemActive(subItem);
                              return (
                                <Link
                                  key={subItem.href}
                                  href={subItem.href}
                                  onClick={onNavigate}
                                  className={`flex items-center gap-3 px-3 py-1.5 rounded-lg text-sm transition-colors ${
                                    active
                                      ? 'bg-purple-600 text-white'
                                      : 'text-slate-400 hover:bg-slate-800 hover:text-white'
                                  }`}
                                >
                                  <subItem.icon className="w-3.5 h-3.5" />
                                  {subItem.label}
                                </Link>
                              );
                            })}
                          </div>
                        )}
                      </div>
                    );
                  }

                  // Regular menu item
                  const menuItem = item as AdminMenuItem;
                  const active = isItemActive(menuItem);
                  return (
                    <Link
                      key={menuItem.href}
                      href={menuItem.href}
                      onClick={onNavigate}
                      className={`flex items-center gap-3 px-3 py-2 rounded-lg text-sm transition-colors ${
                        active
                          ? 'bg-purple-600 text-white'
                          : 'text-slate-400 hover:bg-slate-800 hover:text-white'
                      }`}
                    >
                      <menuItem.icon className="w-4 h-4" />
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

/* ─── Helpers ─────────────────────────────────────────── */

function getRoleLabel(role: string) {
  const roles: Record<string, string> = {
    super_admin: "Super Admin",
    admin: "Administrador",
    analyst: "Analista",
    viewer: "Visualizador",
    oficina_empleo: "Oficina de Empleo",
    usuario: "Usuario",
  };
  return roles[role] || role;
}

function getRoleBadgeColor(role: string) {
  const colors: Record<string, string> = {
    super_admin: "bg-purple-100 text-purple-800",
    admin: "bg-blue-100 text-blue-800",
    analyst: "bg-green-100 text-green-800",
    oficina_empleo: "bg-teal-100 text-teal-800",
    viewer: "bg-gray-100 text-gray-800",
    usuario: "bg-gray-100 text-gray-800",
  };
  return colors[role] || "bg-gray-100 text-gray-800";
}

function isItemVisible(item: NavItem, role: string | undefined, plan: string | undefined): boolean {
  if (item.roles === "*" && !item.plans) return true;
  if (!role) return false;

  // Admins bypass plan check
  const isAdminRole = role === "super_admin" || role === "admin";
  if (isAdminRole && (item.roles === "*" || item.roles.includes(role))) return true;

  // Check role
  if (item.roles !== "*" && !item.roles.includes(role)) return false;

  // Check plan (if specified)
  if (item.plans && !isAdminRole) {
    if (!plan || !item.plans.includes(plan)) return false;
  }

  return true;
}

function isActive(
  pathname: string,
  href: string,
  matchMode: "exact" | "startsWith" = "startsWith"
): boolean {
  if (matchMode === "exact") return pathname === href;
  if (href === "/") return pathname === "/";
  return pathname.startsWith(href);
}

/* ─── Component ───────────────────────────────────────── */

export function GlobalNav() {
  const router = useRouter();
  const pathname = usePathname();
  const [user, setUser] = useState<UserInfo | null>(null);
  const [loading, setLoading] = useState(true);
  const [dropdownOpen, setDropdownOpen] = useState(false);
  const [sheetOpen, setSheetOpen] = useState(false);

  useEffect(() => {
    async function loadUser() {
      try {
        const supabase = createBrowserClient();
        const {
          data: { user: authUser },
        } = await supabase.auth.getUser();

        if (authUser) {
          setUser({
            email: authUser.email || "",
            role: authUser.user_metadata?.role || "viewer",
            plan: authUser.user_metadata?.plan || "free",
            displayName:
              authUser.user_metadata?.display_name ||
              authUser.email?.split("@")[0] ||
              "Usuario",
          });
        }
      } catch {
        // Not authenticated
      } finally {
        setLoading(false);
      }
    }
    loadUser();
  }, []);

  const handleLogout = async () => {
    const supabase = createBrowserClient();
    await supabase.auth.signOut();
    setDropdownOpen(false);
    setSheetOpen(false);
    router.push("/login");
  };

  const visibleItems = NAV_ITEMS.filter((item) =>
    isItemVisible(item, user?.role, user?.plan)
  );

  const isInAdmin = pathname.startsWith("/admin");

  return (
    <>
      <header className="h-14 bg-slate-900 text-white flex items-center px-4 md:px-6 shrink-0 z-40 relative">
        {/* Left: Logo + nav items */}
        <div className="flex items-center gap-1 md:gap-6 flex-1 min-w-0">
          {/* Mobile hamburger */}
          <button
            className="md:hidden p-2 rounded-lg hover:bg-slate-800 transition-colors"
            onClick={() => setSheetOpen(true)}
            aria-label="Abrir menu"
          >
            <Menu className="w-5 h-5" />
          </button>

          {/* Logo */}
          <Link href="/" className="flex items-center gap-2 shrink-0">
            <Image
              src="/logo_mol2.png"
              alt="MOL"
              width={32}
              height={32}
              className="object-contain"
            />
            <span className="font-semibold text-sm hidden sm:inline">MOL</span>
          </Link>

          {/* Desktop nav items */}
          <nav className="hidden md:flex items-center gap-1">
            {visibleItems.map((item) => {
              const active = isActive(pathname, item.href, item.matchMode);
              return (
                <Link
                  key={item.href}
                  href={item.href}
                  className={`flex items-center gap-2 px-3 py-1.5 rounded-md text-sm font-medium transition-colors ${
                    active
                      ? "bg-slate-700 text-white"
                      : "text-slate-300 hover:bg-slate-800 hover:text-white"
                  }`}
                >
                  <item.icon className="w-4 h-4" />
                  {item.label}
                </Link>
              );
            })}
          </nav>
        </div>

        {/* Right: User dropdown */}
        <div className="relative shrink-0">
          {loading ? (
            <div className="w-8 h-8 rounded-full bg-slate-700 animate-pulse" />
          ) : user ? (
            <>
              <button
                onClick={() => setDropdownOpen(!dropdownOpen)}
                className="flex items-center gap-2 px-2 py-1.5 rounded-lg hover:bg-slate-800 transition-colors cursor-pointer"
              >
                <div className="w-7 h-7 rounded-full bg-blue-600 flex items-center justify-center">
                  <User className="w-4 h-4 text-white" />
                </div>
                <span className="text-sm font-medium hidden sm:inline max-w-[120px] truncate">
                  {user.displayName}
                </span>
                <ChevronDown
                  className={`w-3.5 h-3.5 text-slate-400 transition-transform hidden sm:block ${
                    dropdownOpen ? "rotate-180" : ""
                  }`}
                />
              </button>

              {/* Dropdown menu */}
              {dropdownOpen && (
                <div className="absolute right-0 mt-1 w-56 bg-white rounded-lg shadow-lg border border-gray-200 z-50 text-gray-900">
                  <div className="px-4 py-3 border-b border-gray-100">
                    <p className="text-sm font-medium truncate">
                      {user.displayName}
                    </p>
                    <p className="text-xs text-gray-500 truncate">
                      {user.email}
                    </p>
                    <span
                      className={`inline-block text-xs px-2 py-0.5 rounded-full mt-1 ${getRoleBadgeColor(user.role)}`}
                    >
                      {getRoleLabel(user.role)}
                    </span>
                  </div>
                  <div className="py-1">
                    {(user.role === "admin" ||
                      user.role === "super_admin") && (
                      <button
                        onClick={() => {
                          setDropdownOpen(false);
                          router.push("/admin");
                        }}
                        className="w-full flex items-center gap-2 px-4 py-2 text-sm text-purple-600 hover:bg-purple-50 transition-colors cursor-pointer"
                      >
                        <Shield className="w-4 h-4" />
                        Panel Admin
                      </button>
                    )}
                    <button
                      onClick={handleLogout}
                      className="w-full flex items-center gap-2 px-4 py-2 text-sm text-red-600 hover:bg-red-50 transition-colors cursor-pointer"
                    >
                      <LogOut className="w-4 h-4" />
                      Cerrar sesion
                    </button>
                  </div>
                </div>
              )}
            </>
          ) : (
            <Link
              href="/login"
              className="text-sm font-medium text-slate-300 hover:text-white transition-colors px-3 py-1.5"
            >
              Iniciar sesion
            </Link>
          )}
        </div>

        {/* Overlay to close dropdown */}
        {dropdownOpen && (
          <div
            className="fixed inset-0 z-40"
            onClick={() => setDropdownOpen(false)}
          />
        )}
      </header>

      {/* Mobile Sheet */}
      <Sheet open={sheetOpen} onOpenChange={setSheetOpen}>
        <SheetContent side="left" className="w-72 bg-slate-900 text-white border-slate-700 p-0">
          <SheetHeader className="p-4 border-b border-slate-700">
            <SheetTitle className="flex items-center gap-2 text-white">
              <Image
                src="/logo_mol2.png"
                alt="MOL"
                width={28}
                height={28}
                className="object-contain"
              />
              <span className="font-semibold">MOL</span>
            </SheetTitle>
          </SheetHeader>

          {/* Global nav items */}
          <nav className="p-3 space-y-1">
            {visibleItems.map((item) => {
              const active = isActive(pathname, item.href, item.matchMode);
              return (
                <Link
                  key={item.href}
                  href={item.href}
                  onClick={() => setSheetOpen(false)}
                  className={`flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-colors ${
                    active
                      ? "bg-slate-700 text-white"
                      : "text-slate-300 hover:bg-slate-800 hover:text-white"
                  }`}
                >
                  <item.icon className="w-5 h-5" />
                  {item.label}
                </Link>
              );
            })}
          </nav>

          {/* Admin sub-nav (only when in /admin) */}
          {isInAdmin && (
            <div className="border-t border-slate-700 p-3">
              <AdminSidebar pathname={pathname} onNavigate={() => setSheetOpen(false)} />
            </div>
          )}

          {/* User info at bottom */}
          {user && (
            <div className="mt-auto border-t border-slate-700 p-4">
              <div className="flex items-center gap-3 mb-3">
                <div className="w-8 h-8 rounded-full bg-blue-600 flex items-center justify-center shrink-0">
                  <User className="w-4 h-4 text-white" />
                </div>
                <div className="min-w-0">
                  <p className="text-sm font-medium truncate">
                    {user.displayName}
                  </p>
                  <p className="text-xs text-slate-400 truncate">
                    {user.email}
                  </p>
                </div>
              </div>
              <span
                className={`inline-block text-xs px-2 py-0.5 rounded-full mb-3 ${getRoleBadgeColor(user.role)}`}
              >
                {getRoleLabel(user.role)}
              </span>
              <button
                onClick={handleLogout}
                className="w-full flex items-center gap-2 px-3 py-2 text-sm text-red-400 hover:bg-slate-800 rounded-lg transition-colors cursor-pointer"
              >
                <LogOut className="w-4 h-4" />
                Cerrar sesion
              </button>
            </div>
          )}
        </SheetContent>
      </Sheet>
    </>
  );
}

"use client";

import { useState, useEffect } from "react";
import Image from "next/image";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { createBrowserClient } from "@/lib/supabase/browser";

interface UserInfo {
  email: string;
  displayName: string;
  role: string;
}

export function AnimatedNav() {
  const router = useRouter();
  const [scrolled, setScrolled] = useState(false);
  const [mobileOpen, setMobileOpen] = useState(false);
  const [user, setUser] = useState<UserInfo | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const onScroll = () => setScrolled(window.scrollY > 50);
    window.addEventListener("scroll", onScroll, { passive: true });
    return () => window.removeEventListener("scroll", onScroll);
  }, []);

  useEffect(() => {
    async function loadUser() {
      try {
        const supabase = createBrowserClient();
        const { data: { user: authUser } } = await supabase.auth.getUser();

        if (authUser) {
          setUser({
            email: authUser.email || "",
            displayName:
              authUser.user_metadata?.display_name ||
              authUser.email?.split("@")[0] ||
              "Usuario",
            role: authUser.user_metadata?.role || "viewer",
          });
        }
      } catch {
        // No auth available — stay as guest
      } finally {
        setLoading(false);
      }
    }
    loadUser();
  }, []);

  const handleLogout = async () => {
    const supabase = createBrowserClient();
    await supabase.auth.signOut();
    setUser(null);
    setMobileOpen(false);
    router.refresh();
  };

  const dashboardHref =
    user?.role === "admin" || user?.role === "super_admin"
      ? "/admin"
      : "/dashboard";

  return (
    <header
      className="fixed top-0 w-full z-50 transition-all duration-300"
      style={{
        backgroundColor: scrolled
          ? "rgba(10, 22, 40, 0.95)"
          : "transparent",
        backdropFilter: scrolled ? "blur(12px)" : "none",
        borderBottom: scrolled
          ? "1px solid rgba(91, 163, 230, 0.15)"
          : "1px solid transparent",
      }}
    >
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          <Link href="/" className="flex items-center gap-3">
            <Image
              src="/logo_mol_dark.png"
              alt="MOL Logo"
              width={130}
              height={50}
              priority
            />
          </Link>

          <nav className="hidden md:flex items-center gap-8">
            {[
              { href: "#funcionalidades", label: "Funcionalidades" },
              { href: "#datos", label: "Datos" },
              { href: "#acceso", label: "Acceso" },
            ].map((link) => (
              <a
                key={link.href}
                href={link.href}
                className="text-sm font-medium transition-colors"
                style={{ color: "var(--slate-300)" }}
                onMouseEnter={(e) =>
                  (e.currentTarget.style.color = "var(--teal-300)")
                }
                onMouseLeave={(e) =>
                  (e.currentTarget.style.color = "var(--slate-300)")
                }
              >
                {link.label}
              </a>
            ))}
          </nav>

          {/* Desktop auth buttons */}
          <div className="hidden md:flex items-center gap-3">
            {loading ? null : user ? (
              <>
                <span
                  className="text-sm font-medium"
                  style={{ color: "var(--slate-200)" }}
                >
                  {user.displayName}
                </span>
                <Link
                  href={dashboardHref}
                  className="text-sm font-semibold text-white px-5 py-2.5 rounded-lg shadow-lg transition-all hover:shadow-xl"
                  style={{
                    background:
                      "linear-gradient(135deg, var(--teal-500), var(--teal-400))",
                  }}
                >
                  Ir al Dashboard
                </Link>
                <button
                  onClick={handleLogout}
                  className="text-sm font-semibold px-4 py-2 transition-colors cursor-pointer"
                  style={{ color: "var(--slate-400)" }}
                  onMouseEnter={(e) =>
                    (e.currentTarget.style.color = "var(--red-400, #f87171)")
                  }
                  onMouseLeave={(e) =>
                    (e.currentTarget.style.color = "var(--slate-400)")
                  }
                >
                  Cerrar Sesion
                </button>
              </>
            ) : (
              <>
                <Link
                  href="/login"
                  className="text-sm font-semibold px-4 py-2 transition-colors"
                  style={{ color: "var(--slate-200)" }}
                >
                  Iniciar Sesion
                </Link>
                <Link
                  href="/registro"
                  className="text-sm font-semibold text-white px-5 py-2.5 rounded-lg shadow-lg transition-all hover:shadow-xl"
                  style={{
                    background:
                      "linear-gradient(135deg, var(--teal-500), var(--teal-400))",
                  }}
                >
                  Registrarse
                </Link>
              </>
            )}
          </div>

          {/* Mobile hamburger */}
          <button
            className="md:hidden flex flex-col gap-1.5 p-2"
            onClick={() => setMobileOpen(!mobileOpen)}
            aria-label="Menu"
          >
            <span
              className="block w-6 h-0.5 transition-transform"
              style={{
                backgroundColor: "var(--slate-200)",
                transform: mobileOpen
                  ? "rotate(45deg) translate(4px, 4px)"
                  : "none",
              }}
            />
            <span
              className="block w-6 h-0.5 transition-opacity"
              style={{
                backgroundColor: "var(--slate-200)",
                opacity: mobileOpen ? 0 : 1,
              }}
            />
            <span
              className="block w-6 h-0.5 transition-transform"
              style={{
                backgroundColor: "var(--slate-200)",
                transform: mobileOpen
                  ? "rotate(-45deg) translate(4px, -4px)"
                  : "none",
              }}
            />
          </button>
        </div>
      </div>

      {/* Mobile menu */}
      {mobileOpen && (
        <div
          className="md:hidden px-4 pb-4 space-y-3"
          style={{ backgroundColor: "var(--navy-900)" }}
        >
          {[
            { href: "#funcionalidades", label: "Funcionalidades" },
            { href: "#datos", label: "Datos" },
            { href: "#acceso", label: "Acceso" },
          ].map((link) => (
            <a
              key={link.href}
              href={link.href}
              className="block text-sm font-medium py-2"
              style={{ color: "var(--slate-300)" }}
              onClick={() => setMobileOpen(false)}
            >
              {link.label}
            </a>
          ))}
          <div className="flex flex-col gap-3 pt-2">
            {loading ? null : user ? (
              <>
                <span
                  className="text-sm font-medium"
                  style={{ color: "var(--slate-200)" }}
                >
                  {user.displayName}
                </span>
                <Link
                  href={dashboardHref}
                  className="text-sm font-semibold text-white px-5 py-2.5 rounded-lg text-center"
                  style={{
                    background:
                      "linear-gradient(135deg, var(--teal-500), var(--teal-400))",
                  }}
                  onClick={() => setMobileOpen(false)}
                >
                  Ir al Dashboard
                </Link>
                <button
                  onClick={handleLogout}
                  className="text-sm font-semibold px-4 py-2 text-left"
                  style={{ color: "var(--slate-400)" }}
                >
                  Cerrar Sesion
                </button>
              </>
            ) : (
              <>
                <Link
                  href="/login"
                  className="text-sm font-semibold px-4 py-2"
                  style={{ color: "var(--slate-200)" }}
                >
                  Iniciar Sesion
                </Link>
                <Link
                  href="/registro"
                  className="text-sm font-semibold text-white px-5 py-2.5 rounded-lg"
                  style={{
                    background:
                      "linear-gradient(135deg, var(--teal-500), var(--teal-400))",
                  }}
                >
                  Registrarse
                </Link>
              </>
            )}
          </div>
        </div>
      )}
    </header>
  );
}

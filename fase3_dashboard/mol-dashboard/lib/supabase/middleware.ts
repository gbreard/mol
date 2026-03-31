import { createServerClient, type CookieOptions } from "@supabase/ssr";
import { NextResponse, type NextRequest } from "next/server";

// Usuario mock para desarrollo local sin Supabase real
const DEV_MOCK_USER = {
  id: "dev-mock-user-id",
  email: "dev@mol.local",
  user_metadata: { role: "admin", plan: "enterprise" },
  app_metadata: {},
  aud: "authenticated",
  created_at: new Date().toISOString(),
};

export async function updateSession(request: NextRequest) {
  const supabaseResponse = NextResponse.next({ request });

  // Dev bypass: retorna usuario admin mock sin tocar Supabase
  if (process.env.DEV_MOCK_AUTH === "true") {
    const user = DEV_MOCK_USER;

    if (user && request.nextUrl.pathname === "/login") {
      const url = request.nextUrl.clone();
      url.pathname = "/home";
      return NextResponse.redirect(url);
    }

    return supabaseResponse;
  }

  let mutableResponse = supabaseResponse;

  const supabase = createServerClient(
    process.env.NEXT_PUBLIC_SUPABASE_URL!,
    process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!,
    {
      cookies: {
        getAll() {
          return request.cookies.getAll();
        },
        setAll(cookiesToSet: { name: string; value: string; options: CookieOptions }[]) {
          cookiesToSet.forEach(({ name, value }) =>
            request.cookies.set(name, value)
          );
          mutableResponse = NextResponse.next({
            request,
          });
          cookiesToSet.forEach(({ name, value, options }) =>
            mutableResponse.cookies.set(name, value, options)
          );
        },
      },
    }
  );

  const {
    data: { user },
  } = await supabase.auth.getUser();

  // Rutas públicas que no requieren autenticación
  const publicPrefixes = ["/login", "/auth/callback", "/informes", "/precios", "/registro", "/checkout", "/skills", "/para-oficinas", "/mi-futuro-laboral", "/metodologia", "/terminos", "/politica-datos"];
  const publicExact = ["/"];
  const isPublicRoute =
    publicExact.includes(request.nextUrl.pathname) ||
    publicPrefixes.some((route) => request.nextUrl.pathname.startsWith(route));

  // Rutas API manejan su propia autenticación (por header)
  const isApiRoute = request.nextUrl.pathname.startsWith("/api/");

  // Si no hay usuario y no es ruta pública ni API, redirigir a login
  if (!user && !isPublicRoute && !isApiRoute) {
    const url = request.nextUrl.clone();
    url.pathname = "/login";
    return NextResponse.redirect(url);
  }

  // S-04 FIX: Rutas /admin/* requieren rol admin o super_admin en user_metadata
  const isAdminRoute = request.nextUrl.pathname.startsWith("/admin");
  if (isAdminRoute && user) {
    const role = user.user_metadata?.role as string | undefined
    if (role !== 'admin' && role !== 'super_admin') {
      const url = request.nextUrl.clone();
      url.pathname = "/home";
      return NextResponse.redirect(url);
    }
  }

  // Dashboard gating: requiere admin, subscriber, o trial activo
  const isDashboardRoute = request.nextUrl.pathname.startsWith("/dashboard");
  if (isDashboardRoute && user) {
    const role = (user.user_metadata?.role as string) || 'viewer';
    const plan = (user.user_metadata?.plan as string) || 'free';
    const trialStartDate = user.user_metadata?.trial_start_date as string | undefined;

    const isAdminUser = role === 'admin' || role === 'super_admin';
    const isPaidUser = plan === 'pro' || plan === 'enterprise';

    let isTrialActive = false;
    if (plan === 'trial' && trialStartDate) {
      const start = new Date(trialStartDate);
      const diffDays = (Date.now() - start.getTime()) / (1000 * 60 * 60 * 24);
      isTrialActive = diffDays < 7;
    }

    if (!isAdminUser && !isPaidUser && !isTrialActive) {
      const url = request.nextUrl.clone();
      url.pathname = "/home";
      if (plan === 'trial') {
        url.searchParams.set('trial_expired', '1');
      } else {
        url.searchParams.set('no_access', '1');
      }
      return NextResponse.redirect(url);
    }
  }

  // Oficina de Empleo gating: requiere rol oficina_empleo, admin, o super_admin
  const isOficinaRoute = request.nextUrl.pathname.startsWith("/oficina-empleo");
  if (isOficinaRoute && user) {
    const role = (user.user_metadata?.role as string) || 'viewer';
    if (role !== 'oficina_empleo' && role !== 'admin' && role !== 'super_admin') {
      const url = request.nextUrl.clone();
      url.pathname = "/home";
      return NextResponse.redirect(url);
    }
  }

  // Si hay usuario y está en login, redirigir a home
  if (user && request.nextUrl.pathname === "/login") {
    const url = request.nextUrl.clone();
    url.pathname = "/home";
    return NextResponse.redirect(url);
  }

  return mutableResponse;
}

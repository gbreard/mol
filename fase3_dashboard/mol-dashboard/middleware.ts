import { type NextRequest, NextResponse } from "next/server";
import { updateSession } from "@/lib/supabase/middleware";

export async function middleware(request: NextRequest) {
  // S2 dev: bypass total para /oficina-empleo y /empresas
  // TODO: quitar al implementar auth
  if (
    request.nextUrl.pathname.startsWith("/oficina-empleo") ||
    request.nextUrl.pathname.startsWith("/empresas")
  ) {
    return NextResponse.next();
  }
  return await updateSession(request);
}

export const config = {
  matcher: [
    /*
     * Match all request paths except:
     * - _next/static (static files)
     * - _next/image (image optimization files)
     * - favicon.ico (favicon file)
     * - public files (images, etc)
     * - /skills (public page)
     * - /data (public JSON files)
     */
    "/((?!_next/static|_next/image|favicon.ico|skills|data|.*\\.(?:svg|png|jpg|jpeg|gif|webp|json)$).*)",
  ],
};

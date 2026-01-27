import type { Metadata } from "next";
import "./globals.css";
import Navigation from "@/components/Navigation";
import Header from "@/components/Header";

export const metadata: Metadata = {
  title: "MOL - Monitor de Ofertas Laborales",
  description: "Observatorio de Empleo y Dinámica Empresarial - Dashboard de ofertas laborales",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="es">
      <body className="font-sans antialiased bg-gray-50">
        <div className="min-h-screen">
          <Header />
          <Navigation />
          <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
            {children}
          </main>
        </div>
      </body>
    </html>
  );
}

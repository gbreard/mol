import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";
import Navigation from "@/components/Navigation";
import Header from "@/components/Header";
import Sidebar from "@/components/Sidebar";

const inter = Inter({ subsets: ["latin"] });

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
      <body className={`${inter.className} antialiased bg-gray-50`}>
        <div className="min-h-screen">
          <Header />
          <Navigation />
          <div className="flex">
            <Sidebar />
            <main className="flex-1 px-6 py-6">
              {children}
            </main>
          </div>
        </div>
      </body>
    </html>
  );
}

import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Mol - Dashboard de Mercado Laboral",
  description: "Panorama general del mercado laboral, requerimientos y ofertas laborales",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="es">
      <body className="antialiased font-sans">
        {children}
      </body>
    </html>
  );
}

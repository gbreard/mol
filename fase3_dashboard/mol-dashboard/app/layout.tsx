import type { Metadata } from "next";
import "./globals.css";
import { IssueWrapper } from "@/components/issues";

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
        <IssueWrapper>
          {children}
        </IssueWrapper>
      </body>
    </html>
  );
}

import type { Metadata } from "next";
import { DM_Sans, Playfair_Display } from "next/font/google";
import "./globals.css";
import { Toaster } from "sonner";
import { IssueWrapper } from "@/components/issues";

const dmSans = DM_Sans({
  subsets: ["latin"],
  variable: "--font-dm-sans",
  display: "swap",
});

const playfair = Playfair_Display({
  subsets: ["latin"],
  variable: "--font-playfair",
  display: "swap",
});

export const metadata: Metadata = {
  title: "MOL - Monitor de Ofertas Laborales",
  description:
    "Inteligencia del mercado laboral argentino en tiempo real. Análisis de ofertas, competencias y tendencias con clasificación ESCO.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="es">
      <body
        className={`${dmSans.variable} ${playfair.variable} antialiased font-sans`}
      >
        <IssueWrapper>{children}</IssueWrapper>
        <Toaster richColors position="bottom-right" />
      </body>
    </html>
  );
}

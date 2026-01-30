import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Taxonomía ESCO - Skills y Competencias",
  description: "Visualización interactiva de la jerarquía de competencias ESCO",
};

export default function SkillsLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  // Layout simple - hereda html/body del root layout
  return (
    <div className="min-h-screen bg-white antialiased font-sans">
      {children}
    </div>
  );
}

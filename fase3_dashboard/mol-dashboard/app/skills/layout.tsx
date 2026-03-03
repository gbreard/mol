import type { Metadata } from "next";
import { GlobalNav } from "@/components/navigation/GlobalNav";

export const metadata: Metadata = {
  title: "Taxonomía ESCO - Skills y Competencias",
  description: "Visualización interactiva de la jerarquía de competencias ESCO",
};

export default function SkillsLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <div className="min-h-screen bg-white antialiased font-sans flex flex-col">
      <GlobalNav />
      <div className="flex-1">
        {children}
      </div>
    </div>
  );
}

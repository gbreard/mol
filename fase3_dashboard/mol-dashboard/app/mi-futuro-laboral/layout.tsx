import { GlobalNav } from "@/components/navigation/GlobalNav";

export default function MiFuturoLaboralLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-50 to-gray-100 flex flex-col">
      <GlobalNav />
      <main className="flex-1">{children}</main>
    </div>
  );
}

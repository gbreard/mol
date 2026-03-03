import { GlobalNav } from "@/components/navigation/GlobalNav";

export default function InformesLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <div className="min-h-screen flex flex-col">
      <GlobalNav />
      <div className="flex-1">
        {children}
      </div>
    </div>
  );
}

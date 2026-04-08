import { GlobalNav } from '@/components/navigation/GlobalNav'
import { QueryProvider } from '@/lib/query-provider'

export default function VipLayout({ children }: { children: React.ReactNode }) {
  return (
    <QueryProvider>
      <div className="min-h-screen bg-gradient-to-br from-gray-50 to-gray-100 flex flex-col">
        <GlobalNav />
        <main className="flex-1">{children}</main>
      </div>
    </QueryProvider>
  )
}

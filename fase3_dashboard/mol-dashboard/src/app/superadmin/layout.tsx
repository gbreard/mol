'use client'

import Link from 'next/link'
import { usePathname } from 'next/navigation'

const superadminLinks = [
  { href: '/superadmin/metricas', label: 'Metricas', icon: 'chart' },
  { href: '/superadmin/organizaciones', label: 'Organizaciones', icon: 'building' },
  { href: '/superadmin/auditoria', label: 'Auditoria', icon: 'clipboard' },
]

const icons: Record<string, React.ReactNode> = {
  chart: (
    <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
    </svg>
  ),
  building: (
    <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4" />
    </svg>
  ),
  clipboard: (
    <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-3 7h3m-3 4h3m-6-4h.01M9 16h.01" />
    </svg>
  ),
}

export default function SuperAdminLayout({
  children,
}: {
  children: React.ReactNode
}) {
  const pathname = usePathname()

  return (
    <div className="flex min-h-[calc(100vh-64px)]">
      {/* Sidebar */}
      <aside className="w-56 bg-purple-900 text-white flex-shrink-0">
        <div className="p-4">
          <div className="flex items-center gap-2 mb-6">
            <span className="px-2 py-1 text-xs font-bold bg-purple-600 rounded">
              SUPERADMIN
            </span>
          </div>
          <nav className="space-y-1">
            {superadminLinks.map((link) => {
              const isActive = pathname === link.href
              return (
                <Link
                  key={link.href}
                  href={link.href}
                  className={`flex items-center space-x-3 px-3 py-2 rounded-md text-sm font-medium transition-colors ${
                    isActive
                      ? 'bg-purple-700 text-white'
                      : 'text-purple-200 hover:bg-purple-800 hover:text-white'
                  }`}
                >
                  <span className={isActive ? 'text-white' : 'text-purple-400'}>
                    {icons[link.icon]}
                  </span>
                  <span>{link.label}</span>
                </Link>
              )
            })}
          </nav>
        </div>

        {/* Divider */}
        <div className="border-t border-purple-700 my-4 mx-4"></div>

        {/* Link to admin panel */}
        <div className="px-4">
          <Link
            href="/admin/usuarios"
            className="flex items-center space-x-3 px-3 py-2 rounded-md text-sm font-medium text-purple-200 hover:bg-purple-800 hover:text-white"
          >
            <svg className="w-5 h-5 text-purple-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4.354a4 4 0 110 5.292M15 21H3v-1a6 6 0 0112 0v1zm0 0h6v-1a6 6 0 00-9-5.197M13 7a4 4 0 11-8 0 4 4 0 018 0z" />
            </svg>
            <span>Panel Admin</span>
          </Link>
        </div>

        {/* Back to dashboard */}
        <div className="absolute bottom-4 left-4">
          <Link
            href="/"
            className="flex items-center space-x-2 text-sm text-purple-300 hover:text-white"
          >
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 19l-7-7m0 0l7-7m-7 7h18" />
            </svg>
            <span>Volver al dashboard</span>
          </Link>
        </div>
      </aside>

      {/* Main content */}
      <main className="flex-1 bg-gray-50 p-6">
        {children}
      </main>
    </div>
  )
}

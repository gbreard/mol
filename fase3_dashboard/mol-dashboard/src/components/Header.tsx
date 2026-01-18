'use client';

export default function Header() {
  return (
    <header className="bg-white shadow-sm border-b border-gray-200">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between items-center h-16">
          {/* Logo y título */}
          <div className="flex items-center space-x-3">
            <div className="w-10 h-10 bg-blue-600 rounded-lg flex items-center justify-center">
              <span className="text-white font-bold text-lg">M</span>
            </div>
            <div>
              <h1 className="text-xl font-semibold text-gray-900">MOL</h1>
              <p className="text-xs text-gray-500">Monitor de Ofertas Laborales</p>
            </div>
          </div>

          {/* Usuario */}
          <div className="flex items-center space-x-4">
            <span className="text-sm text-gray-600">OEDE</span>
            <div className="flex items-center space-x-2">
              <div className="w-8 h-8 bg-gray-300 rounded-full flex items-center justify-center">
                <span className="text-sm font-medium text-gray-600">DA</span>
              </div>
              <span className="text-sm font-medium text-gray-700">DemoAdministrador</span>
            </div>
          </div>
        </div>
      </div>
    </header>
  );
}

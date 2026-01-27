"use client";

import Image from "next/image";
import { User } from "lucide-react";

export function Header() {
  return (
    <header className="h-20 border-b border-gray-200 bg-gradient-to-r from-white to-gray-50 flex items-center justify-between px-8 shadow-md">
      <div className="flex items-center gap-5">
        <div className="relative w-16 h-16 flex items-center justify-center">
          <Image
            src="/logo_mol2.png"
            alt="Logo MOL"
            width={64}
            height={64}
            className="object-contain"
            priority
          />
        </div>
        <h1 className="text-2xl font-bold text-gray-900 tracking-tight">Monitor de Oferta Laborales</h1>
      </div>

      <div className="flex items-center gap-3 bg-white border border-gray-200 rounded-lg px-4 py-2 shadow-sm hover:shadow-md transition-shadow">
        <div className="bg-blue-600 rounded-full p-2">
          <User className="w-5 h-5 text-white" />
        </div>
        <div className="flex flex-col">
          <span className="text-sm font-semibold text-gray-900">Usuario Demo</span>
          <span className="text-xs text-gray-500">Administrador</span>
        </div>
      </div>
    </header>
  );
}

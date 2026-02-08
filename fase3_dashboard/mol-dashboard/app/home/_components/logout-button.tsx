"use client";

import { createBrowserClient } from "@/lib/supabase/browser";
import { LogOut } from "lucide-react";

export function LogoutButton() {

  const handleLogout = async () => {
    const supabase = createBrowserClient();
    await supabase.auth.signOut();
    window.location.href = "/";
  };

  return (
    <button
      onClick={handleLogout}
      className="flex items-center gap-2 text-sm text-gray-400 hover:text-red-500 transition-colors"
    >
      <LogOut className="w-4 h-4" />
      Salir
    </button>
  );
}

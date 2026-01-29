"use client";

import { useIssues } from "@/contexts/IssueContext";
import { MessageSquare } from "lucide-react";

export function IssueFAB() {
  const { openDrawer, pendingCount, isOpen } = useIssues();

  // Don't show FAB when drawer is open
  if (isOpen) return null;

  return (
    <button
      onClick={() => openDrawer()}
      className="fixed bottom-6 right-6 w-14 h-14 bg-blue-600 hover:bg-blue-700 text-white rounded-full shadow-lg hover:shadow-xl transition-all flex items-center justify-center z-40 group"
      title="Issues y Feedback"
    >
      <MessageSquare className="w-6 h-6 group-hover:scale-110 transition-transform" />

      {/* Badge with pending count */}
      {pendingCount > 0 && (
        <span className="absolute -top-1 -right-1 w-6 h-6 bg-red-500 text-white text-xs font-bold rounded-full flex items-center justify-center border-2 border-white">
          {pendingCount > 9 ? "9+" : pendingCount}
        </span>
      )}
    </button>
  );
}

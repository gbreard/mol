"use client";

import { useIssues } from "@/contexts/IssueContext";
import { Drawer, DrawerContent, DrawerHeader, DrawerTitle, DrawerClose } from "@/components/ui/drawer";
import { Button } from "@/components/ui/button";
import { IssueList } from "./IssueList";
import { IssueForm } from "./IssueForm";
import { X, Plus, ArrowRight, CheckCircle2 } from "lucide-react";
import { useState, useEffect } from "react";
import { Issue } from "@/lib/types";
import { getIssues } from "@/lib/supabase";

export function IssueDrawer() {
  const { isOpen, closeDrawer, pendingIssues, pendingCount, isCreating, setIsCreating, selectedOferta } = useIssues();
  const [recentResolved, setRecentResolved] = useState<Issue[]>([]);

  // Load recent resolved issues
  useEffect(() => {
    if (isOpen) {
      getIssues({ estado: "resuelto" })
        .then((issues) => setRecentResolved(issues.slice(0, 3)))
        .catch(console.error);
    }
  }, [isOpen, pendingIssues]); // Refresh when pending changes

  const handleFormSuccess = () => {
    setIsCreating(false);
  };

  const handleFormCancel = () => {
    setIsCreating(false);
  };

  return (
    <Drawer open={isOpen} onOpenChange={(open) => !open && closeDrawer()} direction="right">
      <DrawerContent className="h-full w-[340px] sm:w-[380px]">
        <DrawerHeader className="border-b pb-4">
          <div className="flex items-center justify-between">
            <DrawerTitle className="text-lg font-bold text-gray-900">
              Issues & Feedback
            </DrawerTitle>
            <DrawerClose asChild>
              <Button variant="ghost" size="sm" className="h-8 w-8 p-0">
                <X className="w-4 h-4" />
              </Button>
            </DrawerClose>
          </div>
        </DrawerHeader>

        <div className="flex-1 overflow-y-auto p-4">
          {isCreating || selectedOferta ? (
            <IssueForm
              onSuccess={handleFormSuccess}
              onCancel={handleFormCancel}
              compact
            />
          ) : (
            <>
              {/* New Issue Button */}
              <Button
                onClick={() => setIsCreating(true)}
                className="w-full mb-4 bg-blue-600 hover:bg-blue-700"
              >
                <Plus className="w-4 h-4 mr-2" />
                Nuevo Issue General
              </Button>

              {/* Pending Issues */}
              <div className="mb-6">
                <h4 className="text-sm font-semibold text-gray-700 mb-3 flex items-center gap-2">
                  <span className="w-2 h-2 bg-yellow-500 rounded-full"></span>
                  Pendientes ({pendingCount})
                </h4>
                <IssueList issues={pendingIssues} compact />
              </div>

              {/* Recent Resolved */}
              {recentResolved.length > 0 && (
                <div className="mb-6">
                  <h4 className="text-sm font-semibold text-gray-500 mb-3 flex items-center gap-2">
                    <CheckCircle2 className="w-4 h-4 text-green-500" />
                    Resueltos recientes
                  </h4>
                  <div className="space-y-2">
                    {recentResolved.map((issue) => (
                      <div
                        key={issue.id}
                        className="flex items-center gap-2 text-sm text-gray-500 py-1"
                      >
                        <span className="w-1.5 h-1.5 bg-green-500 rounded-full"></span>
                        <span className="truncate">{issue.titulo}</span>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* View All Link */}
              <div className="pt-4 border-t">
                <a
                  href="/admin/issues"
                  className="flex items-center justify-center gap-2 text-sm text-blue-600 hover:text-blue-800 font-medium"
                >
                  Ver todos los issues
                  <ArrowRight className="w-4 h-4" />
                </a>
              </div>
            </>
          )}
        </div>
      </DrawerContent>
    </Drawer>
  );
}

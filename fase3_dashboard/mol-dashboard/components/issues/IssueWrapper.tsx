"use client";

import { IssueProvider } from "@/contexts/IssueContext";
import { IssueFAB } from "./IssueFAB";
import { IssueDrawer } from "./IssueDrawer";

export function IssueWrapper({ children }: { children: React.ReactNode }) {
  return (
    <IssueProvider>
      {children}
      <IssueFAB />
      <IssueDrawer />
    </IssueProvider>
  );
}

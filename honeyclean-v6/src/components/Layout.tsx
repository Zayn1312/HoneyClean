import type { ReactNode } from "react";
import { Sidebar } from "./Sidebar";
import { StatusBar } from "./StatusBar";

export function Layout({ children }: { children: ReactNode }) {
  return (
    <div className="h-screen flex flex-col overflow-hidden">
      <div className="flex flex-1 min-h-0">
        <Sidebar />
        <main className="flex-1 overflow-y-auto">
          {children}
        </main>
      </div>
      <StatusBar />
    </div>
  );
}

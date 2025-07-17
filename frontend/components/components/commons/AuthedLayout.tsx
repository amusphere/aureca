import { ReactNode } from "react";
import { SidebarProvider, SidebarTrigger } from "../ui/sidebar";
import AppSidebar from "./AppSidebar";

export default async function AuthedLayout({ children }: { children: ReactNode }) {
  return (
    <SidebarProvider>
      <div className="flex h-screen w-full overflow-hidden bg-background">
        <AppSidebar />
        <main className="flex-1 flex flex-col min-w-0 overflow-hidden">
          {/* Enhanced header with better spacing and visual separation */}
          <div className="flex-shrink-0 px-4 py-3 border-b bg-card/50 backdrop-blur-sm">
            <SidebarTrigger className="hover:bg-secondary/80 transition-colors duration-200" />
          </div>

          {/* Main content area with improved spacing */}
          <div className="flex-1 overflow-y-auto">
            <div className="h-full">
              {children}
            </div>
          </div>
        </main>
      </div>
    </SidebarProvider>
  );
}

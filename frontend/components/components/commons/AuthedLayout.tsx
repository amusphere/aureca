import { ReactNode } from "react";
import { SidebarProvider, SidebarTrigger } from "../ui/sidebar";
import AppSidebar from "./AppSidebar";

export default async function AuthedLayout({ children }: { children: ReactNode }) {
  return (
    <SidebarProvider>
      <div className="flex h-screen w-full overflow-hidden bg-background">
        <AppSidebar />
        <main className="flex-1 flex flex-col min-w-0 overflow-hidden relative">
          {/* Main content area with full height */}
          <div className="flex-1 overflow-y-auto">
            <div className="h-full">
              {children}
            </div>
          </div>

          {/* Floating sidebar trigger in bottom left of main content */}
          <div className="absolute bottom-6 left-6 z-50">
            <SidebarTrigger className="bg-muted hover:bg-muted/80 text-muted-foreground hover:text-foreground shadow-md rounded-full p-3 transition-all duration-200 hover:scale-105" />
          </div>
        </main>
      </div>
    </SidebarProvider>
  );
}

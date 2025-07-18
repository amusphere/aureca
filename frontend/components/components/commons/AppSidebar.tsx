"use client";

import { Home, Settings } from "lucide-react";
import { usePathname } from "next/navigation";

import ClerkUserButton from "@/components/auth/ClerkUserButton";
import EmailPasswordUserButton from "@/components/auth/EmailPasswordUserButton";
import {
  Sidebar,
  SidebarContent,
  SidebarFooter,
  SidebarGroup,
  SidebarGroupContent,
  SidebarGroupLabel,
  SidebarHeader,
  SidebarMenu,
  SidebarMenuButton,
  SidebarMenuItem,
  SidebarSeparator,
} from "@/components/components/ui/sidebar";

const authSystem = process.env.NEXT_PUBLIC_AUTH_SYSTEM;

const items = [
  {
    title: "Home",
    url: "/home",
    icon: Home,
  },
  {
    title: "Settings",
    url: "/settings",
    icon: Settings,
  },
];

export default function AppSidebar() {
  const pathname = usePathname();

  return (
    <Sidebar className="border-r border-sidebar-border/40 bg-gradient-to-b from-sidebar to-sidebar/95" role="navigation" aria-label="メインナビゲーション">
      <SidebarHeader className="px-4 sm:px-7 py-4 sm:py-6 border-b border-sidebar-border/25 bg-sidebar/80 backdrop-blur-sm">
        <div className="flex items-center gap-2 sm:gap-4">
          <div className="flex h-8 w-8 sm:h-9 sm:w-9 items-center justify-center rounded-xl bg-gradient-to-br from-primary to-primary-hover text-primary-foreground shadow-lg shadow-primary/20">
            <Home className="h-3.5 w-3.5 sm:h-4 sm:w-4" />
          </div>
          <div className="flex flex-col gap-0.5 min-w-0">
            <h2 className="text-base sm:text-lg font-semibold text-sidebar-foreground tracking-tight leading-none truncate">
              Task Manager
            </h2>
            <p className="text-xs text-sidebar-foreground/65 font-medium tracking-wide hidden sm:block">
              Organize & Track
            </p>
          </div>
        </div>
      </SidebarHeader>

      <SidebarContent className="px-4 py-6">
        <SidebarGroup className="px-0">
          <SidebarGroupLabel className="px-4 py-3 text-xs font-semibold text-sidebar-foreground/75 uppercase tracking-widest mb-2">
            Navigation
          </SidebarGroupLabel>
          <SidebarGroupContent>
            <SidebarMenu className="space-y-2">
              {items.map((item) => {
                const isActive = pathname === item.url;
                return (
                  <SidebarMenuItem key={item.title}>
                    <SidebarMenuButton
                      asChild
                      isActive={isActive}
                      className={`
                        relative px-4 py-3 rounded-xl transition-all duration-300 ease-out group
                        hover:bg-sidebar-accent/90 hover:text-sidebar-accent-foreground hover:shadow-sm
                        focus-visible:ring-2 focus-visible:ring-sidebar-ring focus-visible:ring-offset-2 focus-visible:ring-offset-sidebar
                        ${isActive
                          ? 'bg-gradient-to-r from-sidebar-accent to-sidebar-accent/80 text-sidebar-accent-foreground font-semibold shadow-md border border-sidebar-border/30 backdrop-blur-sm'
                          : 'text-sidebar-foreground/85 hover:text-sidebar-foreground'
                        }
                      `}
                    >
                      <a
                        href={item.url}
                        className="flex items-center gap-3 sm:gap-4 w-full"
                        aria-current={isActive ? 'page' : undefined}
                      >
                        <item.icon
                          className={`h-4 w-4 transition-all duration-300 ${isActive
                            ? 'text-primary scale-110'
                            : 'text-sidebar-foreground/70 group-hover:text-sidebar-foreground group-hover:scale-105'
                          }`}
                          aria-hidden="true"
                        />
                        <span className="text-sm font-medium tracking-tight leading-none truncate">{item.title}</span>
                        {isActive && (
                          <div
                            className="absolute left-0 top-1/2 -translate-y-1/2 w-1.5 h-8 bg-gradient-to-b from-primary to-primary-hover rounded-r-full shadow-sm"
                            aria-hidden="true"
                          />
                        )}
                      </a>
                    </SidebarMenuButton>
                  </SidebarMenuItem>
                );
              })}
            </SidebarMenu>
          </SidebarGroupContent>
        </SidebarGroup>
      </SidebarContent>

      <SidebarSeparator className="mx-4 bg-sidebar-border/30" />

      <SidebarFooter className="px-4 sm:px-7 py-4 sm:py-5 border-t border-sidebar-border/25 bg-gradient-to-r from-sidebar/90 to-sidebar/95 backdrop-blur-sm">
        <div className="flex items-center justify-between w-full">
          <div className="flex items-center gap-2 sm:gap-4 min-w-0 flex-1">
            <div className="flex items-center gap-2 sm:gap-3 p-1.5 sm:p-2 rounded-lg bg-sidebar-accent/40 border border-sidebar-border/20 backdrop-blur-sm">
              {authSystem === 'clerk' ? (
                <ClerkUserButton />
              ) : (
                <EmailPasswordUserButton />
              )}
            </div>
          </div>
        </div>
      </SidebarFooter>
    </Sidebar>
  );
}

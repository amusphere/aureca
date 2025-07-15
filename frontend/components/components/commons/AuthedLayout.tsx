import { User } from "@/types/User";
import { apiGet } from "@/utils/api";
import { redirect } from "next/navigation";
import { ReactNode } from "react";
import { SidebarProvider, SidebarTrigger } from "../ui/sidebar";
import AppSidebar from "./AppSidebar";

export default async function AuthedLayout({ children }: { children: ReactNode }) {
  const { data, error } = await apiGet<User>("/users/me");
  if (error && error.status === 401) {
    return redirect("/");
  }

  return (
    <SidebarProvider>
      <AppSidebar user={data} />
      <main className="flex-1 flex flex-col h-screen">
        <div className="flex-shrink-0">
          <SidebarTrigger />
        </div>
        <div className="flex-1 overflow-y-auto">{children}</div>
      </main>
    </SidebarProvider>
  );
}

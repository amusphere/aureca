"use client"

import { User } from "@/types/User";
import { UserButton } from "@clerk/nextjs";
import Link from "next/link";
import { Avatar, AvatarFallback, AvatarImage } from "../ui/avatar";
import { DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuLabel, DropdownMenuSeparator, DropdownMenuTrigger } from "../ui/dropdown-menu";

type Props = {
  user: User;
};

export default function AppSidebarFooterContent({ user }: Props) {
  const authSystem = process.env.NEXT_PUBLIC_AUTH_SYSTEM;

  if (!user) {
    return (
      <div className="flex items-center gap-4 p-2 w-full">
        <div className="text-sm text-gray-500">Loading...</div>
      </div>
    );
  }

  return (
    <div className="flex items-center gap-4 p-2 w-full">
      {authSystem === "email_password" && (
        <DropdownMenu>
          <DropdownMenuTrigger className="flex items-center gap-2 w-full">
            <Avatar>
              <AvatarImage src="https://picsum.photos/100" alt="avatar" />
              <AvatarFallback>
                {user.name?.charAt(0).toUpperCase() || 'U'}
                {user.name?.charAt(1).toUpperCase() || 'S'}
              </AvatarFallback>
            </Avatar>
            <span className="text-sm font-medium">{user.name || 'User'}</span>
          </DropdownMenuTrigger>
          <DropdownMenuContent>
            <DropdownMenuLabel>My Account</DropdownMenuLabel>
            <DropdownMenuSeparator />
            <DropdownMenuItem>
              <Link href="/api/auth/signout" className="text-red-500">
                Signout
              </Link>
            </DropdownMenuItem>
          </DropdownMenuContent>
        </DropdownMenu>
      )}
      {authSystem === "clerk" && (
        <UserButton appearance={{
          elements: {
            userButtonBox: {
              flexDirection: "row-reverse",
            },
          },
        }} showName={true} />
      )}
    </div>
  )
}

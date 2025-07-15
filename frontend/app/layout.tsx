import { ClerkProvider } from "@clerk/nextjs";
import type { Metadata } from "next";
import { Toaster } from "sonner";
import "./globals.css";

export const metadata: Metadata = {
  title: process.env.APP_NAME,
  description: "",
};

const authSystem = process.env.NEXT_PUBLIC_AUTH_SYSTEM;

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  const content = (
    <html lang="en">
      <body className="antialiased">
        <div className="bg-gray-100 min-h-screen">
          {children}
        </div>
        <Toaster richColors expand={true} />
      </body>
    </html>
  );

  if (authSystem === 'clerk') {
    return <ClerkProvider>{content}</ClerkProvider>;
  }

  return content;
}

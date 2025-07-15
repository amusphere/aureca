import { ClerkProvider } from "@clerk/nextjs";
import type { Metadata } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import { Toaster } from "sonner";
import "./globals.css";

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: process.env.APP_NAME,
  description: "",
};

const authSystem = process.env.NEXT_PUBLIC_AUTH_SYSTEM;
const clerkPublishableKey = process.env.NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY;

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  const content = (
    <html lang="en">
      <body className={`${geistSans.variable} ${geistMono.variable} antialiased`}>
        <div className="bg-gray-100 min-h-screen">
          {children}
        </div>
        <Toaster richColors expand={true} />
      </body>
    </html>
  );

  // Only use ClerkProvider if we have clerk auth system AND a valid publishable key
  if (authSystem === 'clerk' && clerkPublishableKey && clerkPublishableKey !== 'your-clerk-publishable-key') {
    return <ClerkProvider>{content}</ClerkProvider>;
  }

  return content;
}

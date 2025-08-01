import { ClerkProvider } from "@clerk/nextjs";
import type { Metadata } from "next";
import { Toaster } from "sonner";
import "./globals.css";


export const metadata: Metadata = {
  title: process.env.NEXT_PUBLIC_APP_NAME,
  description: "",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="ja">
      <head>
        <meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover" />
        <meta name="theme-color" content="#3b82f6" />
        <meta name="color-scheme" content="light dark" />
      </head>
      <body className="antialiased">

        <ClerkProvider>
          <div className="bg-gray-100 min-h-screen" id="app-root">
            <main id="main-content" tabIndex={-1}>
              {children}
            </main>
          </div>
        </ClerkProvider>

        {/* Screen reader live region for announcements */}
        <div
          id="sr-announcements"
          aria-live="polite"
          aria-atomic="true"
          className="sr-only"
        />

        {/* Toast notifications with proper ARIA live region */}
        <div aria-live="polite" aria-atomic="true">
          <Toaster
            richColors
            expand={true}
            position="top-right"
            toastOptions={{
              duration: 5000,
              style: {
                background: 'var(--background)',
                color: 'var(--foreground)',
                border: '1px solid var(--border)',
              },
            }}
          />
        </div>
      </body>
    </html>
  );
}

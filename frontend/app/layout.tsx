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
    <html lang="ja">
      <head>
        <meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover" />
        <meta name="theme-color" content="#3b82f6" />
        <meta name="color-scheme" content="light dark" />
      </head>
      <body className="antialiased">
        {/* Skip link for keyboard navigation */}
        <a href="#main-content" className="skip-link">
          メインコンテンツにスキップ
        </a>

        <div className="bg-gray-100 min-h-screen" id="app-root">
          <main id="main-content" tabIndex={-1}>
            {children}
          </main>
        </div>

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

        {/* Screen reader announcements */}
        <div
          id="sr-announcements"
          aria-live="assertive"
          aria-atomic="true"
          className="sr-only"
        ></div>
      </body>
    </html>
  );

  if (authSystem === 'clerk') {
    return <ClerkProvider>{content}</ClerkProvider>;
  }

  return content;
}

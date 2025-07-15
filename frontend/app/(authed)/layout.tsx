import AuthedLayout from "@/components/components/commons/AuthedLayout";

// Force dynamic rendering since this layout uses cookies for auth
export const dynamic = 'force-dynamic';

export default function NoAuthLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <AuthedLayout>
      {children}
    </AuthedLayout>
  );
}

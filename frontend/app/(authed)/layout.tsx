import AuthedLayout from "@/components/components/commons/AuthedLayout";


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

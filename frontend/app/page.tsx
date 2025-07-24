import ClerkLoginPage from "@/components/auth/ClerkLoginPage";

// Force dynamic rendering to ensure environment variables are read at runtime
export const dynamic = 'force-dynamic';


export default async function RootPage() {
  return <ClerkLoginPage />;
}

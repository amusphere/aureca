import ClerkLoginPage from "@/components/auth/ClerkLoginPage";
import EmailPasswordLoginPage from "@/components/auth/EmailPasswordLoginPage";

// Force dynamic rendering to ensure environment variables are read at runtime
export const dynamic = 'force-dynamic';


export default async function RootPage() {
  const authSystem = process.env.NEXT_PUBLIC_AUTH_SYSTEM;

  if (authSystem === "clerk") {
    return <ClerkLoginPage />;
  }

  return <EmailPasswordLoginPage />;
}

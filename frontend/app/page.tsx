import AuthedLayout from "@/components/components/commons/AuthedLayout";
import ClerkLoginPage from "@/components/pages/ClerkLoginPage";
import EmailPasswordLoginPage from "@/components/pages/EmailPasswordLoginPage";
import HomePage from "@/components/pages/HomePage";
import { SignedIn, SignedOut } from "@clerk/nextjs";

// Force dynamic rendering to ensure environment variables are read at runtime
export const dynamic = 'force-dynamic';


export default async function RootPage() {
  const authSystem = process.env.NEXT_PUBLIC_AUTH_SYSTEM;

  if (authSystem === "email_password") {
    return <EmailPasswordLoginPage />;
  }

  if (authSystem === "clerk") {
    return (
      <>
        <SignedOut>
          <ClerkLoginPage />
        </SignedOut>
        <SignedIn>
          <AuthedLayout>
            <HomePage />
          </AuthedLayout>
        </SignedIn>
      </>
    );
  }

  // フォールバック: 環境変数が設定されていない場合
  console.error("NEXT_PUBLIC_AUTH_SYSTEM environment variable is not properly set:", authSystem);
  return <EmailPasswordLoginPage />;
}

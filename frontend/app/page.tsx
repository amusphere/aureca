import AuthedLayout from "@/components/components/commons/AuthedLayout";
import ClerkLoginPage from "@/components/pages/ClerkLoginPage";
import EmailPasswordLoginPage from "@/components/pages/EmailPasswordLoginPage";
import HomePage from "@/components/pages/HomePage";
import { User } from "@/types/User";
import { apiGet } from "@/utils/api";
import { SignedIn, SignedOut } from "@clerk/nextjs";
import { redirect } from "next/navigation";

// Force dynamic rendering since this route uses cookies for auth
export const dynamic = 'force-dynamic';


export default async function RootPage() {
  const authSystem = process.env.NEXT_PUBLIC_AUTH_SYSTEM;

  // Check if the user is already logged in
  if (authSystem === "email_password") {
    const { data } = await apiGet<User>("/users/me");
    if (data && data.uuid) {
      redirect("/home");
      return;
    }

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
}

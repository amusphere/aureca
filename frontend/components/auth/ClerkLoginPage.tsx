import AuthedLayout from "@/components/components/commons/AuthedLayout";
import HomePage from "@/components/pages/HomePage";
import { SignedIn, SignedOut } from "@clerk/nextjs";
import ClerkLoginForm from "./ClerkLoginForm";

export default function ClerkLoginPage() {
  return (
    <>
      <SignedOut>
        <ClerkLoginForm />
      </SignedOut>
      <SignedIn>
        <AuthedLayout>
          <HomePage />
        </AuthedLayout>
      </SignedIn>
    </>
  );
}

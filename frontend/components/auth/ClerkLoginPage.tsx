import AuthedLayout from "@/components/components/commons/AuthedLayout";
import { Button } from "@/components/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/components/ui/card";
import HomePage from "@/components/pages/HomePage";
import { SignedIn, SignedOut, SignInButton } from "@clerk/nextjs";

export default function ClerkLoginPage() {
  return (
    <>
      <SignedOut>
        <div className="flex flex-col items-center justify-center min-h-screen">
          <Card className="w-1/4 text-center">
            <CardHeader>
              <CardTitle className="text-2xl my-2">
                {process.env.APP_NAME}
              </CardTitle>
              <CardDescription>
                A template for building Next.js applications.
              </CardDescription>
            </CardHeader>
            <CardContent>
              <SignInButton mode="modal" signUpFallbackRedirectUrl="/api/users/create">
                <Button className="w-full">
                  Log In
                </Button>
              </SignInButton>
            </CardContent>
          </Card>
        </div>
      </SignedOut>
      <SignedIn>
        <AuthedLayout>
          <HomePage />
        </AuthedLayout>
      </SignedIn>
    </>
  );
}

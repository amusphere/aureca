import LoginForm from "../components/forms/LoginForm";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "../components/ui/card";

export default function EmailPasswordLoginPage() {
  return (
    <>
      <div className="flex flex-col items-center justify-center min-h-screen px-4">
        <Card className="w-full max-w-md mx-auto text-center">
          <CardHeader className="px-4 sm:px-6">
            <CardTitle className="text-xl sm:text-2xl my-2">
              {process.env.APP_NAME}
            </CardTitle>
            <CardDescription className="text-sm sm:text-base">
              Your AI assistant is here to support you.
            </CardDescription>
          </CardHeader>
          <CardContent className="px-4 sm:px-6">
            <LoginForm />
          </CardContent>
        </Card>
      </div>
    </>
  );
}

"use client";

import { useEffect, useState, Suspense } from "react";
import { useForm } from "react-hook-form";
import { useSearchParams } from "next/navigation";
import { toast } from "sonner";
import { Button } from "@/components/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/components/ui/card";
import {
  Form,
  FormControl,
  FormField,
  FormItem,
  FormMessage,
} from "@/components/components/ui/form";
import { Input } from "@/components/components/ui/input";

interface ResetPasswordFormValues {
  new_password: string;
  confirm_password: string;
}

function ResetPasswordForm() {
  const searchParams = useSearchParams();
  const [token, setToken] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [isSuccess, setIsSuccess] = useState(false);
  const [isError, setIsError] = useState(false);

  const form = useForm<ResetPasswordFormValues>({
    defaultValues: {
      new_password: "",
      confirm_password: "",
    },
  });

  useEffect(() => {
    const tokenParam = searchParams.get("token");
    if (tokenParam) {
      setToken(tokenParam);
    } else {
      setIsError(true);
      toast.error("Invalid link. Please request a new password reset.");
    }
  }, [searchParams]);

  const onSubmit = async (data: ResetPasswordFormValues) => {
    if (data.new_password !== data.confirm_password) {
      form.setError("confirm_password", {
        type: "manual",
        message: "Passwords do not match",
      });
      return;
    }

    if (!token) {
      toast.error("Token not found. Please request a new password reset.");
      return;
    }

    setIsSubmitting(true);
    try {
      const res = await fetch("/api/auth/reset-password", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          token,
          new_password: data.new_password,
        }),
      });

      const responseData = await res.json();

      if (res.ok && responseData.success) {
        setIsSuccess(true);
        toast.success("Password has been successfully updated.");
      } else {
        let errorMessage = "An error occurred while resetting your password.";
        if (responseData.error) {
          errorMessage = typeof responseData.error === 'object' && responseData.error.detail
            ? responseData.error.detail
            : String(responseData.error);
        }
        toast.error(errorMessage);
      }
    } catch (error) {
      toast.error("An error occurred while sending your request.");
    } finally {
      setIsSubmitting(false);
    }
  };

  if (isError) {
    return (
      <div className="flex flex-col items-center justify-center min-h-screen">
        <Card className="w-1/4 text-center">
          <CardHeader>
            <CardTitle className="text-2xl my-2">Error</CardTitle>
            <CardDescription>
              Invalid password reset link.
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              <p className="text-sm text-muted-foreground">
                The link is invalid or has expired.
                Please request a new password reset link.
              </p>
              <Button
                className="w-full"
                onClick={() => window.location.href = "/auth/forgot-password"}
              >
                Reset Password
              </Button>
            </div>
          </CardContent>
        </Card>
      </div>
    );
  }

  return (
    <div className="flex flex-col items-center justify-center min-h-screen">
      <Card className="w-1/4 text-center">
        <CardHeader>
          <CardTitle className="text-2xl my-2">Set New Password</CardTitle>
          <CardDescription>
            Enter a new password for your account.
          </CardDescription>
        </CardHeader>
        <CardContent>
          {isSuccess ? (
            <div className="space-y-4">
              <p className="text-sm text-muted-foreground">
                Your password has been successfully updated. You can now log in with your new password.
              </p>
              <Button
                className="w-full"
                onClick={() => window.location.href = "/"}
              >
                Login
              </Button>
            </div>
          ) : (
            <Form {...form}>
              <form
                onSubmit={form.handleSubmit(onSubmit)}
                className="space-y-4 w-full"
              >
                <FormField
                  control={form.control}
                  name="new_password"
                  rules={{
                    required: "Password is required",
                    minLength: {
                      value: 8,
                      message: "Password must be at least 8 characters",
                    },
                  }}
                  render={({ field }) => (
                    <FormItem>
                      <FormControl>
                        <Input
                          {...field}
                          type="password"
                          placeholder="New password"
                          disabled={isSubmitting}
                        />
                      </FormControl>
                      <FormMessage />
                    </FormItem>
                  )}
                />
                <FormField
                  control={form.control}
                  name="confirm_password"
                  rules={{
                    required: "Password confirmation is required",
                  }}
                  render={({ field }) => (
                    <FormItem>
                      <FormControl>
                        <Input
                          {...field}
                          type="password"
                          placeholder="Confirm password"
                          disabled={isSubmitting}
                        />
                      </FormControl>
                      <FormMessage />
                    </FormItem>
                  )}
                />
                <Button
                  type="submit"
                  className="w-full"
                  disabled={isSubmitting}
                >
                  {isSubmitting ? "Processing..." : "Update Password"}
                </Button>
              </form>
            </Form>
          )}
        </CardContent>
      </Card>
    </div>
  );
}

export default function ResetPasswordPage() {
  return (
    <Suspense fallback={<div className="flex items-center justify-center min-h-screen">Loading...</div>}>
      <ResetPasswordForm />
    </Suspense>
  );
}

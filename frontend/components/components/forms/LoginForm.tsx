"use client";

import { useState } from "react";
import { useForm } from "react-hook-form";
import { toast } from "sonner";
import { Button } from "../ui/button";
import { Form, FormField } from "../ui/form";
import { Input } from "../ui/input";

interface LoginFormValues {
  email: string;
  password: string;
}

export default function LoginForm() {
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [submitError, setSubmitError] = useState<string | null>(null);

  const form = useForm<LoginFormValues>({
    defaultValues: {
      email: "",
      password: "",
    },
    mode: "onBlur", // Validate on blur for better UX
  });

  const { formState: { errors, isValid } } = form;

  const onSubmit = async (data: LoginFormValues) => {
    setIsSubmitting(true);
    setSubmitError(null);

    try {
      const res = await fetch("/api/auth/signin", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(data),
      });

      const result = await res.json();

      if (result.success) {
        toast.success("ログインしました");
        window.location.href = "/home";
      } else {
        const errorMessage = "ログインに失敗しました。メールアドレスとパスワードを確認してください。";
        setSubmitError(errorMessage);
        toast.error(errorMessage);
      }
    } catch {
      const errorMessage = "ネットワークエラーが発生しました。しばらく後でお試しください。";
      setSubmitError(errorMessage);
      toast.error(errorMessage);
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <Form {...form}>
      <form
        onSubmit={form.handleSubmit(onSubmit)}
        className="space-y-4 w-full"
        noValidate
        aria-label="ログインフォーム"
      >
        {/* Form-level error message */}
        {submitError && (
          <div
            role="alert"
            aria-live="polite"
            className="p-3 text-sm text-error bg-error/10 border border-error/20 rounded-lg"
          >
            {submitError}
          </div>
        )}

        <FormField
          control={form.control}
          name="email"
          rules={{
            required: "メールアドレスを入力してください",
            pattern: {
              value: /^[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}$/i,
              message: "有効なメールアドレスを入力してください"
            }
          }}
          render={({ field }) => (
            <div className="space-y-1">
              <label htmlFor="email" className="text-sm font-medium text-foreground">
                メールアドレス <span className="text-error" aria-label="必須">*</span>
              </label>
              <Input
                {...field}
                id="email"
                type="email"
                placeholder="example@email.com"
                required
                aria-invalid={!!errors.email}
                aria-describedby={errors.email ? "email-error" : undefined}
                error={!!errors.email}
                autoComplete="email"
                className="w-full"
              />
              {errors.email && (
                <p
                  id="email-error"
                  role="alert"
                  className="text-sm text-error"
                >
                  {errors.email.message}
                </p>
              )}
            </div>
          )}
        />

        <FormField
          control={form.control}
          name="password"
          rules={{
            required: "パスワードを入力してください",
            minLength: {
              value: 6,
              message: "パスワードは6文字以上で入力してください"
            }
          }}
          render={({ field }) => (
            <div className="space-y-1">
              <label htmlFor="password" className="text-sm font-medium text-foreground">
                パスワード <span className="text-error" aria-label="必須">*</span>
              </label>
              <Input
                {...field}
                id="password"
                type="password"
                placeholder="パスワードを入力"
                required
                aria-invalid={!!errors.password}
                aria-describedby={errors.password ? "password-error" : undefined}
                error={!!errors.password}
                autoComplete="current-password"
                className="w-full"
              />
              {errors.password && (
                <p
                  id="password-error"
                  role="alert"
                  className="text-sm text-error"
                >
                  {errors.password.message}
                </p>
              )}
            </div>
          )}
        />

        <div className="flex flex-col space-y-4 pt-2">
          <Button
            type="submit"
            className="w-full"
            disabled={isSubmitting || !isValid}
            aria-busy={isSubmitting}
            aria-describedby={submitError ? "submit-error" : undefined}
          >
            {isSubmitting ? "ログイン中..." : "ログイン"}
          </Button>

          <div className="text-center">
            <a
              href="/auth/forgot-password"
              className="text-sm text-primary hover:underline focus-ring rounded"
              aria-label="パスワードを忘れた場合のリセットページへ移動"
            >
              パスワードを忘れましたか？
            </a>
          </div>
        </div>
      </form>
    </Form>
  );
}

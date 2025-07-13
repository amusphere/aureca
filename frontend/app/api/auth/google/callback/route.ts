"use server";

import { apiPost } from "@/utils/api";
import { NextRequest, NextResponse } from "next/server";

export async function GET(request: NextRequest) {
  try {
    const { searchParams } = new URL(request.url);
    const code = searchParams.get("code");
    const state = searchParams.get("state");
    const error = searchParams.get("error");

    // エラーの場合
    if (error) {
      console.error("Google OAuth error:", error);
      const domain = process.env.FRONTEND_URL || "http://localhost:3000";
      const redirectUrl = new URL(`/home?error=${encodeURIComponent(error)}`, domain);
      return NextResponse.redirect(redirectUrl.toString(), 302);
    }

    // 認証コードがない場合
    if (!code || !state) {
      console.error("Missing code or state parameter");
      const domain = process.env.FRONTEND_URL || "http://localhost:3000";
      const redirectUrl = new URL("/home?error=missing_parameters", domain);
      return NextResponse.redirect(redirectUrl.toString(), 302);
    }

    // バックエンドにコールバック処理を委任
    const { error: apiError } = await apiPost("/google/callback", {
      code,
      state,
    });

    if (apiError) {
      console.error("Backend callback error:", apiError);
      const domain = process.env.FRONTEND_URL || "http://localhost:3000";
      const redirectUrl = new URL(`/home?error=${encodeURIComponent(apiError.message)}`, domain);
      return NextResponse.redirect(redirectUrl.toString(), 302);
    }

    // 成功時はダッシュボードにリダイレクト
    const domain = process.env.FRONTEND_URL || "http://localhost:3000";
    const redirectUrl = new URL("/home?connected=true", domain);
    return NextResponse.redirect(redirectUrl.toString(), 302);

  } catch (error) {
    console.error("Callback processing error:", error);
    const domain = process.env.FRONTEND_URL || "http://localhost:3000";
    const redirectUrl = new URL("/home?error=callback_failed", domain);
    return NextResponse.redirect(redirectUrl.toString(), 302);
  }
}

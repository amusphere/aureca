"use server";

import { apiPost } from "@/utils/api";
import { NextRequest, NextResponse } from "next/server";

const DOMAIN = process.env.FRONTEND_URL || "http://localhost:3000";

export async function GET(request: NextRequest) {
  try {
    const { searchParams } = new URL(request.url);
    const code = searchParams.get("code");
    const state = searchParams.get("state");
    const error = searchParams.get("error");

    // エラーの場合
    if (error) {
      console.error("Google OAuth error:", error);
      const redirectUrl = new URL(`/?error=${encodeURIComponent(error)}`, DOMAIN);
      return NextResponse.redirect(redirectUrl.toString(), 302);
    }

    // 認証コードがない場合
    if (!code || !state) {
      console.error("Missing code or state parameter");
      const redirectUrl = new URL("/?error=missing_parameters", DOMAIN);
      return NextResponse.redirect(redirectUrl.toString(), 302);
    }

    // バックエンドにコールバック処理を委任
    const { error: apiError } = await apiPost("/google/callback", {
      code,
      state,
    });

    if (apiError) {
      console.error("Backend callback error:", apiError);
      const redirectUrl = new URL(`/?error=${encodeURIComponent(apiError.message)}`, DOMAIN);
      return NextResponse.redirect(redirectUrl.toString(), 302);
    }

    // 成功時はダッシュボードにリダイレクト
    const redirectUrl = new URL("/?connected=true", DOMAIN);
    return NextResponse.redirect(redirectUrl.toString(), 302);

  } catch (error) {
    console.error("Callback processing error:", error);
    const redirectUrl = new URL("/?error=callback_failed", DOMAIN);
    return NextResponse.redirect(redirectUrl.toString(), 302);
  }
}

import { apiDelete, apiPost } from "@/utils/api";
import { NextResponse } from "next/server";

export async function GET() {
  // Redirect from clerk in signin flow
  await apiPost("/users");

  const domain = process.env.FRONTEND_URL || "http://localhost:3000";
  const redirectUrl = new URL("/", domain);

  return NextResponse.redirect(redirectUrl.toString(), 302);
}

export async function DELETE() {
  try {
    // バックエンドのDELETE /api/users/meエンドポイントを呼び出し
    const response = await apiDelete("/users");

    if (response.error) {
      console.error("Backend delete error:", response.error);
      return NextResponse.json(
        { error: response.error.message || "Failed to delete user" },
        { status: response.error.status || 500 }
      );
    }

    return NextResponse.json(
      { message: "User deleted successfully" },
      { status: 200 }
    );
  } catch (error) {
    console.error("Failed to delete user:", error);

    return NextResponse.json(
      { error: "Failed to delete user" },
      { status: 500 }
    );
  }
}
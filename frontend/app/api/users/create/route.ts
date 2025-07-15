import { apiPost } from "@/utils/api";
import { NextResponse } from "next/server";

export async function GET() {
  // Redirect from clerk in signin flow
  try {
    await apiPost("/users/create");
  } catch (error) {
    console.error("Error creating user:", error);
  }

  const domain = process.env.FRONTEND_URL || "http://localhost:3000";
  const redirectUrl = new URL("/", domain);

  return NextResponse.redirect(redirectUrl.toString(), 302);
}

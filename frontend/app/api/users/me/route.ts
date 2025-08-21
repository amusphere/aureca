import { UserWithSubscription } from "@/types/User";
import { apiGet } from "@/utils/api";
import { NextResponse } from "next/server";

export async function GET() {
  const { data, error } = await apiGet<UserWithSubscription>("/users/me");

  if (error || !data) {
    return NextResponse.json(
      { error: "Unauthorized" },
      { status: 401 }
    );
  }

  return NextResponse.json(data, { status: 200 });
}

import { apiPost } from "@/utils/api";
import { NextResponse } from "next/server";


export async function POST() {
  const res = await apiPost('/ai/generate-from-all', {});

  if (res.data) {
    return NextResponse.json(res.data);
  }
  if (res.error) {
    return NextResponse.json({ error: res.error }, { status: res.error.status || 500 });
  }

  return NextResponse.json(res);
}

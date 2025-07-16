import { apiPost } from "@/utils/api";
import { NextResponse } from "next/server";


export async function POST() {
  const res = await apiPost('/ai/generate-from-all', {});
  return NextResponse.json(res);
}

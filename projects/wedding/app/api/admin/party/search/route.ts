import { NextRequest, NextResponse } from "next/server";
import { searchPartiesAdmin } from "@/lib/db";

export async function GET(req: NextRequest) {
  const pw = req.nextUrl.searchParams.get("pw");
  if (pw !== process.env.ADMIN_PASSWORD) {
    return NextResponse.json({ error: "unauthorized" }, { status: 401 });
  }

  const q = req.nextUrl.searchParams.get("q") ?? "";
  if (!q.trim()) return NextResponse.json([]);

  const results = await searchPartiesAdmin(q);
  return NextResponse.json(results);
}

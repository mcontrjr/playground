import { NextRequest, NextResponse } from "next/server";
import { getMealTableRows } from "@/lib/db";

export async function GET(req: NextRequest) {
  const pw = req.nextUrl.searchParams.get("pw");
  if (pw !== process.env.ADMIN_PASSWORD) {
    return NextResponse.json({ error: "unauthorized" }, { status: 401 });
  }
  const rows = await getMealTableRows();
  return NextResponse.json(rows);
}

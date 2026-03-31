import { NextRequest, NextResponse } from "next/server";
import { generateIcs } from "@/lib/calendar";

export async function GET(
  _req: NextRequest,
  { params }: { params: Promise<{ id: string }> }
) {
  await params; // Next.js 15 requires awaiting params
  const ics = generateIcs();
  return new NextResponse(ics, {
    headers: {
      "Content-Type": "text/calendar; charset=utf-8",
      "Content-Disposition": `attachment; filename="wedding.ics"`,
    },
  });
}

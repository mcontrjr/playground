import { NextRequest, NextResponse } from "next/server";
import { getAllRsvps } from "@/lib/db";

export async function GET(req: NextRequest) {
  const pass = req.nextUrl.searchParams.get("pw") ?? req.headers.get("x-admin-password");
  if (pass !== process.env.ADMIN_PASSWORD) {
    return new NextResponse("Unauthorized", { status: 401 });
  }

  const rsvps = await getAllRsvps();
  const lines = ["Party,Guest Name,Meal,RSVP Date"];
  for (const r of rsvps) {
    for (const m of r.meals) {
      lines.push(`"${r.partyName}","${m.guestName}","${m.meal}","${r.createdAt}"`);
    }
  }

  return new NextResponse(lines.join("\n"), {
    headers: {
      "Content-Type": "text/csv",
      "Content-Disposition": `attachment; filename="rsvps.csv"`,
    },
  });
}

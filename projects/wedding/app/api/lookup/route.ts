import { NextRequest, NextResponse } from "next/server";
import { z } from "zod";
import { searchInvitees } from "@/lib/db";
import { rateLimit } from "@/lib/rateLimit";
import { WEDDING } from "@/lib/config";

const Schema = z.object({ name: z.string().min(2).max(100) });

export async function POST(req: NextRequest) {
  const ip = req.headers.get("x-forwarded-for") ?? "unknown";
  if (!rateLimit(ip)) {
    return NextResponse.json({ error: "Too many requests" }, { status: 429 });
  }

  // Deadline check
  if (new Date() > new Date(WEDDING.deadlineISO)) {
    return NextResponse.json({ error: "rsvp_closed" }, { status: 403 });
  }

  const body = Schema.safeParse(await req.json());
  if (!body.success) {
    return NextResponse.json({ error: "Invalid name" }, { status: 400 });
  }

  const parties = await searchInvitees(body.data.name);
  return NextResponse.json({ parties });
}

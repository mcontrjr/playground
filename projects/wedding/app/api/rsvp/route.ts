import { NextRequest, NextResponse } from "next/server";
import { z } from "zod";
import { saveRsvp, getPartyByUuid } from "@/lib/db";
import { WEDDING } from "@/lib/config";

const Schema = z.object({
  partyUuid: z.string().uuid(),
  guests: z.array(
    z.object({
      guestName: z.string().min(1).max(100),
      meal: z.enum(["steak", "fish", "chicken", "vegetarian"]),
    })
  ).min(1).max(10),
});

export async function POST(req: NextRequest) {
  if (new Date() > new Date(WEDDING.deadlineISO)) {
    return NextResponse.json({ error: "rsvp_closed" }, { status: 403 });
  }

  const body = Schema.safeParse(await req.json());
  if (!body.success) {
    return NextResponse.json({ error: body.error.flatten() }, { status: 400 });
  }

  const party = await getPartyByUuid(body.data.partyUuid);
  if (!party) {
    return NextResponse.json({ error: "party_not_found" }, { status: 404 });
  }

  const rsvpId = await saveRsvp({ partyId: party.id, guests: body.data.guests });
  return NextResponse.json({ rsvpId });
}

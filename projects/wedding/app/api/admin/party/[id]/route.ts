import { NextRequest, NextResponse } from "next/server";
import { getPartyWithMeals, updatePartyMeals, updatePartyMaxGuests } from "@/lib/db";
import type { GuestMeal } from "@/lib/types";

function auth(req: NextRequest): boolean {
  const pw = req.nextUrl.searchParams.get("pw") ?? req.headers.get("x-admin-pw");
  return pw === process.env.ADMIN_PASSWORD;
}

export async function GET(req: NextRequest, { params }: { params: { id: string } }) {
  if (!auth(req)) return NextResponse.json({ error: "unauthorized" }, { status: 401 });

  const id = Number(params.id);
  if (!Number.isFinite(id)) return NextResponse.json({ error: "invalid id" }, { status: 400 });

  const data = await getPartyWithMeals(id);
  if (!data) return NextResponse.json({ error: "not found" }, { status: 404 });

  return NextResponse.json(data);
}

export async function PATCH(req: NextRequest, { params }: { params: { id: string } }) {
  if (!auth(req)) return NextResponse.json({ error: "unauthorized" }, { status: 401 });

  const id = Number(params.id);
  if (!Number.isFinite(id)) return NextResponse.json({ error: "invalid id" }, { status: 400 });

  const body = await req.json() as { maxGuests?: number; guests?: GuestMeal[] };

  try {
    if (typeof body.maxGuests === "number") {
      await updatePartyMaxGuests(id, body.maxGuests);
    }
    if (Array.isArray(body.guests) && body.guests.length > 0) {
      await updatePartyMeals(id, body.guests);
    }
    return NextResponse.json({ ok: true });
  } catch (e) {
    const msg = e instanceof Error ? e.message : "unknown error";
    return NextResponse.json({ error: msg }, { status: 500 });
  }
}

import { createClient } from "@libsql/client";
import type { Party, RsvpPayload, RsvpSummary, GuestMeal, Meal } from "./types";

function getClient() {
  return createClient({
    url:       process.env.DATABASE_URL!,
    authToken: process.env.DATABASE_AUTH_TOKEN,
  });
}

// ─── Invitee Lookup ────────────────────────────────────────────────────────

export async function searchInvitees(query: string): Promise<Party[]> {
  const db = getClient();
  const like = `%${query.trim()}%`;
  const rs = await db.execute({
    sql: `
      SELECT p.id, p.name, p.max_guests, p.invite_code, p.uuid,
             GROUP_CONCAT(i.name, '||') AS members
      FROM   parties  p
      JOIN   invitees i ON i.party_id = p.id
      WHERE  p.name LIKE ? OR i.name LIKE ?
      GROUP  BY p.id
      LIMIT  6
    `,
    args: [like, like],
  });

  return rs.rows.map((r) => ({
    id:         Number(r.id),
    name:       String(r.name),
    maxGuests:  Number(r.max_guests),
    inviteCode: r.invite_code ? String(r.invite_code) : null,
    uuid:       r.uuid ? String(r.uuid) : null,
    members:    String(r.members).split("||").filter(Boolean),
  }));
}

export async function getPartyById(id: number): Promise<Party | null> {
  const db = getClient();
  const rs = await db.execute({
    sql: `
      SELECT p.id, p.name, p.max_guests, p.invite_code, p.uuid,
             GROUP_CONCAT(i.name, '||') AS members
      FROM   parties p
      JOIN   invitees i ON i.party_id = p.id
      WHERE  p.id = ?
      GROUP  BY p.id
    `,
    args: [id],
  });
  if (!rs.rows[0]) return null;
  const r = rs.rows[0];
  return {
    id:         Number(r.id),
    name:       String(r.name),
    maxGuests:  Number(r.max_guests),
    inviteCode: r.invite_code ? String(r.invite_code) : null,
    uuid:       r.uuid ? String(r.uuid) : null,
    members:    String(r.members).split("||").filter(Boolean),
  };
}

export async function getPartyByUuid(uuid: string): Promise<Party | null> {
  const db = getClient();
  const rs = await db.execute({
    sql: `
      SELECT p.id, p.name, p.max_guests, p.invite_code, p.uuid,
             GROUP_CONCAT(i.name, '||') AS members
      FROM   parties p
      JOIN   invitees i ON i.party_id = p.id
      WHERE  p.uuid = ?
      GROUP  BY p.id
    `,
    args: [uuid],
  });
  if (!rs.rows[0]) return null;
  const r = rs.rows[0];
  return {
    id:         Number(r.id),
    name:       String(r.name),
    maxGuests:  Number(r.max_guests),
    inviteCode: r.invite_code ? String(r.invite_code) : null,
    uuid:       r.uuid ? String(r.uuid) : null,
    members:    String(r.members).split("||").filter(Boolean),
  };
}

export async function hasRsvpdByUuid(uuid: string): Promise<boolean> {
  const db = getClient();
  const rs = await db.execute({
    sql: `
      SELECT r.id FROM rsvps r
      JOIN   parties p ON p.id = r.party_id
      WHERE  p.uuid = ?
      LIMIT  1
    `,
    args: [uuid],
  });
  return rs.rows.length > 0;
}

// ─── RSVP ────────────────────────────────────────────────────────────────

export async function hasRsvpd(partyId: number): Promise<boolean> {
  const db = getClient();
  const rs = await db.execute({
    sql:  "SELECT id FROM rsvps WHERE party_id = ? LIMIT 1",
    args: [partyId],
  });
  return rs.rows.length > 0;
}

export async function saveRsvp(payload: RsvpPayload): Promise<number> {
  const db = getClient();
  const tx = await db.transaction("write");
  try {
    // Upsert — allow editing before deadline
    await tx.execute({
      sql:  "DELETE FROM rsvps WHERE party_id = ?",
      args: [payload.partyId],
    });
    const result = await tx.execute({
      sql:  "INSERT INTO rsvps (party_id, attending) VALUES (?, 1)",
      args: [payload.partyId],
    });
    const rsvpId = Number(result.lastInsertRowid);
    for (const g of payload.guests) {
      await tx.execute({
        sql:  "INSERT INTO meal_selections (rsvp_id, guest_name, meal) VALUES (?,?,?)",
        args: [rsvpId, g.guestName, g.meal],
      });
    }
    await tx.commit();
    return rsvpId;
  } catch (e) {
    await tx.rollback();
    throw e;
  }
}

// ─── Admin ───────────────────────────────────────────────────────────────

export async function getMealTotals(): Promise<Record<Meal, number>> {
  const db = getClient();
  const rs = await db.execute(
    "SELECT meal, COUNT(*) as count FROM meal_selections GROUP BY meal"
  );
  const totals = { steak: 0, fish: 0, chicken: 0, vegetarian: 0 };
  for (const r of rs.rows) {
    totals[r.meal as Meal] = Number(r.count);
  }
  return totals;
}

export async function getAllRsvps(): Promise<RsvpSummary[]> {
  const db = getClient();
  const rs = await db.execute(`
    SELECT r.id, p.name AS party_name, r.created_at,
           ms.guest_name, ms.meal
    FROM   rsvps r
    JOIN   parties p ON p.id = r.party_id
    JOIN   meal_selections ms ON ms.rsvp_id = r.id
    ORDER  BY r.created_at DESC, p.name, ms.guest_name
  `);

  const map = new Map<number, RsvpSummary>();
  for (const row of rs.rows) {
    const id = Number(row.id);
    if (!map.has(id)) {
      map.set(id, {
        id,
        partyName:  String(row.party_name),
        guestCount: 0,
        meals:      [],
        createdAt:  String(row.created_at),
      });
    }
    const entry = map.get(id)!;
    entry.meals.push({ guestName: String(row.guest_name), meal: row.meal as Meal });
    entry.guestCount++;
  }
  return [...map.values()];
}

export async function getPendingParties(): Promise<string[]> {
  const db = getClient();
  const rs = await db.execute(`
    SELECT name FROM parties
    WHERE  id NOT IN (SELECT party_id FROM rsvps)
    ORDER  BY name
  `);
  return rs.rows.map((r) => String(r.name));
}

// ─── Admin Dashboard ─────────────────────────────────────────────────────────
// Note: @libsql/client handles both local SQLite (DATABASE_URL=file:local.db)
// and Turso cloud (DATABASE_URL=libsql://...). No separate client needed.

export async function getAdminStats(): Promise<{
  confirmed: number;
  remaining: number;
  totalGuests: number;
}> {
  const db = getClient();
  const [confirmedRs, totalPartiesRs, guestRs] = await Promise.all([
    db.execute("SELECT COUNT(*) AS n FROM rsvps"),
    db.execute("SELECT COUNT(*) AS n FROM parties"),
    db.execute("SELECT COUNT(*) AS n FROM meal_selections"),
  ]);
  const confirmed = Number(confirmedRs.rows[0].n);
  const totalParties = Number(totalPartiesRs.rows[0].n);
  return {
    confirmed,
    remaining: totalParties - confirmed,
    totalGuests: Number(guestRs.rows[0].n),
  };
}

export async function getMealTableRows(): Promise<
  Array<{ partyId: number; partyName: string; guestName: string; meal: Meal }>
> {
  const db = getClient();
  const rs = await db.execute(`
    SELECT p.id AS party_id, p.name AS party_name, ms.guest_name, ms.meal
    FROM   meal_selections ms
    JOIN   rsvps r ON r.id = ms.rsvp_id
    JOIN   parties p ON p.id = r.party_id
    ORDER  BY p.name, ms.guest_name
  `);
  return rs.rows.map((r) => ({
    partyId:   Number(r.party_id),
    partyName: String(r.party_name),
    guestName: String(r.guest_name),
    meal:      r.meal as Meal,
  }));
}

export async function searchPartiesAdmin(query: string): Promise<
  Array<{ id: number; name: string; maxGuests: number; confirmed: boolean; uuid: string | null }>
> {
  const db = getClient();
  const like = `%${query.trim()}%`;
  const rs = await db.execute({
    sql: `
      SELECT p.id, p.name, p.max_guests, p.uuid,
             CASE WHEN r.id IS NOT NULL THEN 1 ELSE 0 END AS confirmed
      FROM   parties p
      LEFT   JOIN rsvps r ON r.party_id = p.id
      WHERE  p.name LIKE ?
      ORDER  BY p.name
      LIMIT  10
    `,
    args: [like],
  });
  return rs.rows.map((r) => ({
    id:        Number(r.id),
    name:      String(r.name),
    maxGuests: Number(r.max_guests),
    confirmed: Number(r.confirmed) === 1,
    uuid:      r.uuid ? String(r.uuid) : null,
  }));
}

export async function getPartyWithMeals(partyId: number): Promise<{
  party: Party & { uuid: string | null };
  meals: GuestMeal[] | null;
} | null> {
  const party = await getPartyById(partyId);
  if (!party) return null;

  const db = getClient();
  const rs = await db.execute({
    sql: `
      SELECT ms.guest_name, ms.meal
      FROM   meal_selections ms
      JOIN   rsvps r ON r.id = ms.rsvp_id
      WHERE  r.party_id = ?
      ORDER  BY ms.guest_name
    `,
    args: [partyId],
  });

  const meals = rs.rows.length > 0
    ? rs.rows.map((r) => ({ guestName: String(r.guest_name), meal: r.meal as Meal }))
    : null;

  return { party, meals };
}

export async function updatePartyMeals(partyId: number, guests: GuestMeal[]): Promise<void> {
  const db = getClient();
  const tx = await db.transaction("write");
  try {
    // Get the existing rsvp for this party
    const rsvpRs = await tx.execute({
      sql:  "SELECT id FROM rsvps WHERE party_id = ? LIMIT 1",
      args: [partyId],
    });
    if (!rsvpRs.rows[0]) throw new Error("No RSVP found for party");
    const rsvpId = Number(rsvpRs.rows[0].id);

    await tx.execute({ sql: "DELETE FROM meal_selections WHERE rsvp_id = ?", args: [rsvpId] });
    for (const g of guests) {
      await tx.execute({
        sql:  "INSERT INTO meal_selections (rsvp_id, guest_name, meal) VALUES (?,?,?)",
        args: [rsvpId, g.guestName, g.meal],
      });
    }
    await tx.commit();
  } catch (e) {
    await tx.rollback();
    throw e;
  }
}

export async function updatePartyMaxGuests(partyId: number, maxGuests: number): Promise<void> {
  const db = getClient();
  await db.execute({
    sql:  "UPDATE parties SET max_guests = ? WHERE id = ?",
    args: [maxGuests, partyId],
  });
}

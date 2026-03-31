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
      SELECT p.id, p.name, p.max_guests, p.invite_code,
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
    members:    String(r.members).split("||").filter(Boolean),
  }));
}

export async function getPartyById(id: number): Promise<Party | null> {
  const db = getClient();
  const rs = await db.execute({
    sql: `
      SELECT p.id, p.name, p.max_guests, p.invite_code,
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
    id:        Number(r.id),
    name:      String(r.name),
    maxGuests: Number(r.max_guests),
    inviteCode: r.invite_code ? String(r.invite_code) : null,
    members:   String(r.members).split("||").filter(Boolean),
  };
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

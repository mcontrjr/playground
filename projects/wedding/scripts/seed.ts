import { createClient } from "@libsql/client";
import { parse } from "csv-parse/sync";
import fs from "fs";
import * as dotenv from "dotenv";

dotenv.config({ path: ".env.local" });

const db = createClient({
  url:       process.env.DATABASE_URL!,
  authToken: process.env.DATABASE_AUTH_TOKEN,
});

type Row = { party_name: string; member_name: string; max_guests: string; invite_code: string };

async function seed() {
  const csv  = fs.readFileSync("invitees.csv", "utf8");
  const rows = parse(csv, { columns: true, skip_empty_lines: true }) as Row[];

  const parties = new Map<string, { name: string; maxGuests: number; code: string }>();
  for (const r of rows) {
    if (!parties.has(r.invite_code)) {
      parties.set(r.invite_code, {
        name:      r.party_name,
        maxGuests: Number(r.max_guests),
        code:      r.invite_code,
      });
    }
  }

  for (const [, p] of parties) {
    const result = await db.execute({
      sql:  "INSERT OR IGNORE INTO parties(name, max_guests, invite_code) VALUES(?,?,?)",
      args: [p.name, p.maxGuests, p.code],
    });
    let partyId = Number(result.lastInsertRowid);

    // If already existed, look it up
    if (partyId === 0) {
      const rs = await db.execute({ sql: "SELECT id FROM parties WHERE invite_code = ?", args: [p.code] });
      partyId = Number(rs.rows[0].id);
    }

    const members = rows.filter((r) => r.invite_code === p.code).map((r) => r.member_name);
    for (const name of members) {
      await db.execute({
        sql:  "INSERT OR IGNORE INTO invitees(party_id, name) VALUES(?,?)",
        args: [partyId, name],
      });
    }
    console.log(`✓ ${p.name} (${members.length} members)`);
  }

  console.log(`\nSeeded ${parties.size} parties.`);
}

seed().catch(console.error);

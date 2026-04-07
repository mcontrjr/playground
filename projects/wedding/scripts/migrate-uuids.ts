/**
 * Adds a `uuid` column to `parties` (if not already present) and
 * backfills any rows that don't have one yet.
 *
 * Safe to run multiple times.
 */
import { createClient } from "@libsql/client";
import * as dotenv from "dotenv";
import { randomUUID } from "crypto";

dotenv.config({ path: ".env.local" });

const db = createClient({
  url:       process.env.DATABASE_URL!,
  authToken: process.env.DATABASE_AUTH_TOKEN,
});

async function migrate() {
  // Add column if it doesn't exist yet
  // Note: SQLite ALTER TABLE ADD COLUMN does not support inline UNIQUE — add index separately
  try {
    await db.execute("ALTER TABLE parties ADD COLUMN uuid TEXT");
    console.log("✓ Added uuid column to parties");
  } catch {
    // Column already exists — that's fine
    console.log("  uuid column already exists, skipping ALTER");
  }

  // Create unique index if missing (safe to run multiple times)
  await db.execute(
    "CREATE UNIQUE INDEX IF NOT EXISTS idx_parties_uuid ON parties(uuid)"
  );

  // Fetch all parties missing a UUID
  const rs = await db.execute("SELECT id FROM parties WHERE uuid IS NULL");
  let filled = 0;
  for (const row of rs.rows) {
    await db.execute({
      sql:  "UPDATE parties SET uuid = ? WHERE id = ?",
      args: [randomUUID(), Number(row.id)],
    });
    filled++;
  }

  console.log(`✓ Backfilled ${filled} parties with UUIDs`);
  console.log("Migration complete.");
}

migrate().catch(console.error);

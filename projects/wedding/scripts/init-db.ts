import { createClient } from "@libsql/client";
import * as dotenv from "dotenv";

dotenv.config({ path: ".env.local" });

const db = createClient({
  url: process.env.DATABASE_URL!,
  authToken: process.env.DATABASE_AUTH_TOKEN,
});

async function init() {
  await db.executeMultiple(`
    CREATE TABLE IF NOT EXISTS parties (
      id          INTEGER PRIMARY KEY AUTOINCREMENT,
      name        TEXT    NOT NULL,
      max_guests  INTEGER NOT NULL DEFAULT 2,
      invite_code TEXT    UNIQUE
    );

    CREATE TABLE IF NOT EXISTS invitees (
      id        INTEGER PRIMARY KEY AUTOINCREMENT,
      party_id  INTEGER NOT NULL REFERENCES parties(id) ON DELETE CASCADE,
      name      TEXT    NOT NULL
    );

    CREATE TABLE IF NOT EXISTS rsvps (
      id          INTEGER PRIMARY KEY AUTOINCREMENT,
      party_id    INTEGER NOT NULL REFERENCES parties(id),
      attending   INTEGER NOT NULL DEFAULT 1,
      created_at  TEXT    NOT NULL DEFAULT (datetime('now')),
      UNIQUE(party_id)
    );

    CREATE TABLE IF NOT EXISTS meal_selections (
      id         INTEGER PRIMARY KEY AUTOINCREMENT,
      rsvp_id    INTEGER NOT NULL REFERENCES rsvps(id) ON DELETE CASCADE,
      guest_name TEXT    NOT NULL,
      meal       TEXT    NOT NULL CHECK(meal IN ('steak','fish','chicken','vegetarian'))
    );

    CREATE INDEX IF NOT EXISTS idx_invitees_name ON invitees(name COLLATE NOCASE);
    CREATE INDEX IF NOT EXISTS idx_parties_code  ON parties(invite_code);
    CREATE INDEX IF NOT EXISTS idx_rsvps_party   ON rsvps(party_id);
  `);

  console.log("✓ Schema initialized.");
}

init().catch(console.error);

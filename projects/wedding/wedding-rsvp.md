# Wedding RSVP — Implementation Guide
### Stack: Next.js 15 · TypeScript · Turso · Vercel

---

## Design Language

Drawn from the physical invitation card:

| Token | Value | Usage |
|-------|-------|-------|
| `--ivory` | `#F5F0E8` | Page background |
| `--ink` | `#1C1C1C` | Primary text, borders |
| `--ink-muted` | `#6B6560` | Secondary text, placeholders |
| `--ink-faint` | `#D4CFC8` | Dividers, inactive states |
| `--surface` | `#FDFAF5` | Card backgrounds |
| Font — Display | `Cormorant Garamond` | Headings (the serif soul) |
| Font — Body | `Jost` | Body, labels, inputs (spaced, light) |
| Letter spacing | `0.12em` on uppercase | All caps labels, nav |
| Motion | `ease: [0.25, 0, 0, 1]` | Slow, intentional transitions |

**Aesthetic rule:** No gradients. No shadows heavier than `0 1px 3px rgba(0,0,0,0.06)`. No rounded corners larger than `4px`. White space is the decoration.

---

## Table of Contents

1. [Project Setup](#1-project-setup)
2. [Project Structure](#2-project-structure)
3. [Database Schema & Turso Setup](#3-database-schema--turso-setup)
4. [Environment Variables](#4-environment-variables)
5. [Data Layer — lib/](#5-data-layer)
6. [API Routes](#6-api-routes)
7. [Pages — The 5-Step RSVP Flow](#7-pages--the-5-step-rsvp-flow)
8. [Shared Components](#8-shared-components)
9. [Design System & Global Styles](#9-design-system--global-styles)
10. [Hosting — Vercel](#10-hosting--vercel)
11. [Admin Dashboard](#11-admin-dashboard)
12. [QR Code Generation](#12-qr-code-generation)
13. [Calendar Integration](#13-calendar-integration)
14. [Testing with Playwright](#14-testing-with-playwright)
15. [Seeding Invitees from CSV](#15-seeding-invitees-from-csv)
16. [Go-Live Checklist](#16-go-live-checklist)

---

## 1. Project Setup

```bash
npx create-next-app@latest wedding-rsvp \
  --typescript \
  --tailwind \
  --app \
  --no-src-dir \
  --import-alias "@/*"

cd wedding-rsvp

# Core dependencies
npm install @libsql/client zod ics date-fns

# Dev / test
npm install -D @playwright/test dotenv-cli
npx playwright install chromium

# Fonts (via next/font — no external request at runtime)
# Cormorant Garamond + Jost are loaded in layout.tsx via Google Fonts
```

---

## 2. Project Structure

```
wedding-rsvp/
├── app/
│   ├── layout.tsx                  # Root layout, fonts, CSS vars
│   ├── globals.css                 # Design tokens, resets, base styles
│   ├── rsvp/
│   │   ├── page.tsx                # Step 1 — Name lookup
│   │   ├── party/page.tsx          # Step 2 — Party selection
│   │   ├── guests/page.tsx         # Step 3 — Guest count & names
│   │   ├── meals/page.tsx          # Step 4 — Meal selection
│   │   └── confirm/page.tsx        # Step 5 — Confirmation
│   ├── admin/
│   │   └── page.tsx                # Password-protected meal summary
│   └── api/
│       ├── lookup/route.ts         # POST: search invitees by name
│       ├── rsvp/route.ts           # POST: save full RSVP
│       ├── calendar/[id]/route.ts  # GET: .ics file download
│       └── admin/export/route.ts   # GET: CSV export for caterer
├── components/
│   ├── StepLayout.tsx              # Shared page shell with progress
│   ├── GuestStepper.tsx            # +/– guest count control
│   ├── MealCard.tsx                # Single meal option card
│   ├── PartyCard.tsx               # Party selection card
│   └── CalendarButtons.tsx         # Apple + Google calendar links
├── lib/
│   ├── db.ts                       # Turso client, all queries
│   ├── types.ts                    # Shared TypeScript types
│   ├── calendar.ts                 # ICS generation
│   ├── config.ts                   # Wedding details (name, date, etc.)
│   └── rateLimit.ts                # In-memory rate limiter
├── scripts/
│   └── seed.ts                     # Load invitees.csv → Turso
├── tests/
│   ├── rsvp-flow.spec.ts           # Full E2E happy path
│   ├── validation.spec.ts          # Edge cases & validation
│   └── admin.spec.ts               # Admin page protection
├── playwright.config.ts
├── next.config.ts
└── .env.local
```

---

## 3. Database Schema & Turso Setup

```bash
# Install Turso CLI
brew install tursodatabase/tap/turso

# Create database
turso db create wedding-rsvp
turso db show wedding-rsvp      # copy the URL
turso db tokens create wedding-rsvp  # copy the auth token

# Open shell and run schema
turso db shell wedding-rsvp
```

```sql
-- Paste this into the turso shell

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
  attending   INTEGER NOT NULL DEFAULT 1,  -- 1 = yes, 0 = no
  created_at  TEXT    NOT NULL DEFAULT (datetime('now')),
  UNIQUE(party_id)                          -- one RSVP per party
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
```

---

## 4. Environment Variables

**`.env.local`**
```bash
# Turso
DATABASE_URL=libsql://your-db-name.turso.io
DATABASE_AUTH_TOKEN=your-token-here

# Wedding config (used in calendar, emails, copy)
NEXT_PUBLIC_WEDDING_COUPLE="Sarah & James"
NEXT_PUBLIC_WEDDING_DATE_DISPLAY="Saturday, September 20th, 2025"
WEDDING_DATE_ISO="2025-09-20T16:00:00"
NEXT_PUBLIC_WEDDING_LOCATION="The Grand Ballroom"
NEXT_PUBLIC_WEDDING_ADDRESS="123 Wilshire Blvd, Beverly Hills, CA 90210"
NEXT_PUBLIC_RSVP_DEADLINE_DISPLAY="September 1st, 2025"
RSVP_DEADLINE_ISO="2025-09-01T23:59:59"

# Admin
ADMIN_PASSWORD=choose-a-strong-password

# Base URL (for ICS links in emails)
NEXT_PUBLIC_BASE_URL=https://yourdomain.com
```

---

## 5. Data Layer

**`lib/types.ts`**
```typescript
export type Meal = "steak" | "fish" | "chicken" | "vegetarian";

export interface Party {
  id: number;
  name: string;
  maxGuests: number;
  inviteCode: string | null;
  members: string[];
}

export interface GuestMeal {
  guestName: string;
  meal: Meal;
}

export interface RsvpPayload {
  partyId: number;
  guests: GuestMeal[];
}

export interface RsvpSummary {
  id: number;
  partyName: string;
  guestCount: number;
  meals: GuestMeal[];
  createdAt: string;
}
```

**`lib/config.ts`**
```typescript
export const WEDDING = {
  couple:        process.env.NEXT_PUBLIC_WEDDING_COUPLE    ?? "The Wedding",
  dateDisplay:   process.env.NEXT_PUBLIC_WEDDING_DATE_DISPLAY ?? "",
  dateISO:       process.env.WEDDING_DATE_ISO              ?? "",
  location:      process.env.NEXT_PUBLIC_WEDDING_LOCATION  ?? "",
  address:       process.env.NEXT_PUBLIC_WEDDING_ADDRESS   ?? "",
  deadlineDisplay: process.env.NEXT_PUBLIC_RSVP_DEADLINE_DISPLAY ?? "",
  deadlineISO:   process.env.RSVP_DEADLINE_ISO             ?? "2099-01-01",
  baseUrl:       process.env.NEXT_PUBLIC_BASE_URL          ?? "http://localhost:3000",
} as const;

export const MEAL_OPTIONS = [
  { id: "steak",       label: "Steak",       description: "Filet mignon, medium" },
  { id: "fish",        label: "Fish",         description: "Pan-seared salmon"   },
  { id: "chicken",     label: "Chicken",      description: "Herb-roasted breast" },
  { id: "vegetarian",  label: "Vegetarian",   description: "Garden risotto"      },
] as const satisfies { id: Meal; label: string; description: string }[];
```

**`lib/db.ts`**
```typescript
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
```

**`lib/rateLimit.ts`**
```typescript
// Simple in-memory rate limiter — good enough for a wedding site
const store = new Map<string, { count: number; reset: number }>();

export function rateLimit(ip: string, limit = 10, windowMs = 60_000): boolean {
  const now = Date.now();
  const entry = store.get(ip);
  if (!entry || now > entry.reset) {
    store.set(ip, { count: 1, reset: now + windowMs });
    return true; // allowed
  }
  if (entry.count >= limit) return false; // blocked
  entry.count++;
  return true;
}
```

---

## 6. API Routes

**`app/api/lookup/route.ts`**
```typescript
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
```

**`app/api/rsvp/route.ts`**
```typescript
import { NextRequest, NextResponse } from "next/server";
import { z } from "zod";
import { saveRsvp } from "@/lib/db";
import { WEDDING } from "@/lib/config";

const Schema = z.object({
  partyId: z.number().int().positive(),
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

  const rsvpId = await saveRsvp(body.data);
  return NextResponse.json({ rsvpId });
}
```

**`app/api/calendar/[id]/route.ts`**
```typescript
import { NextRequest, NextResponse } from "next/server";
import { generateIcs } from "@/lib/calendar";

export async function GET(
  _req: NextRequest,
  { params }: { params: { id: string } }
) {
  const ics = generateIcs();
  return new NextResponse(ics, {
    headers: {
      "Content-Type": "text/calendar; charset=utf-8",
      "Content-Disposition": `attachment; filename="wedding.ics"`,
    },
  });
}
```

**`app/api/admin/export/route.ts`**
```typescript
import { NextRequest, NextResponse } from "next/server";
import { getAllRsvps } from "@/lib/db";

export async function GET(req: NextRequest) {
  const pass = req.headers.get("x-admin-password");
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
```

---

## 7. Pages — The 5-Step RSVP Flow

### Global Layout

**`app/layout.tsx`**
```tsx
import type { Metadata } from "next";
import { Cormorant_Garamond, Jost } from "next/font/google";
import "./globals.css";
import { WEDDING } from "@/lib/config";

const cormorant = Cormorant_Garamond({
  subsets: ["latin"],
  weight: ["300", "400", "500", "600"],
  style: ["normal", "italic"],
  variable: "--font-display",
});

const jost = Jost({
  subsets: ["latin"],
  weight: ["300", "400", "500"],
  variable: "--font-body",
});

export const metadata: Metadata = {
  title: `RSVP — ${WEDDING.couple}`,
  description: `Kindly reply to your invitation to ${WEDDING.couple}'s wedding.`,
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" className={`${cormorant.variable} ${jost.variable}`}>
      <body>{children}</body>
    </html>
  );
}
```

### Step 1 — Name Lookup

**`app/rsvp/page.tsx`**
```tsx
import StepLayout from "@/components/StepLayout";
import LookupForm from "./LookupForm";
import { WEDDING } from "@/lib/config";

export default function RsvpPage({ searchParams }: { searchParams: { ref?: string } }) {
  return (
    <StepLayout step={1} title="R S V P">
      <p className="body-text text-center mb-10">
        kindly reply by {WEDDING.deadlineDisplay}
      </p>
      <LookupForm inviteRef={searchParams.ref} />
    </StepLayout>
  );
}
```

**`app/rsvp/LookupForm.tsx`** (Client Component)
```tsx
"use client";
import { useState } from "react";
import { useRouter } from "next/navigation";
import type { Party } from "@/lib/types";
import PartyCard from "@/components/PartyCard";

export default function LookupForm({ inviteRef }: { inviteRef?: string }) {
  const [name, setName] = useState("");
  const [parties, setParties] = useState<Party[]>([]);
  const [status, setStatus] = useState<"idle" | "loading" | "found" | "empty" | "closed">("idle");
  const router = useRouter();

  async function handleSearch(e: React.FormEvent) {
    e.preventDefault();
    setStatus("loading");
    setParties([]);
    const res = await fetch("/api/lookup", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ name }),
    });
    if (res.status === 403) { setStatus("closed"); return; }
    const data = await res.json();
    if (!data.parties?.length) { setStatus("empty"); return; }
    setParties(data.parties);
    setStatus("found");
  }

  function selectParty(party: Party) {
    const params = new URLSearchParams({
      partyId: String(party.id),
      partyName: party.name,
      maxGuests: String(party.maxGuests),
      members: party.members.join("||"),
    });
    router.push(`/rsvp/guests?${params}`);
  }

  return (
    <div>
      <form onSubmit={handleSearch} className="form-stack">
        <div className="field-group">
          <label className="field-label">Your name</label>
          <input
            type="text"
            value={name}
            onChange={(e) => setName(e.target.value)}
            placeholder="as written on your invitation"
            className="field-input"
            autoComplete="name"
            autoFocus
            required
            minLength={2}
          />
        </div>
        <button type="submit" className="btn-primary" disabled={status === "loading"}>
          {status === "loading" ? "searching…" : "find my invitation"}
        </button>
      </form>

      {status === "empty" && (
        <p className="status-message mt-6">
          We couldn't find that name. Please check your invitation or reach out to us directly.
        </p>
      )}
      {status === "closed" && (
        <p className="status-message mt-6">
          RSVPs have closed. Please contact us directly if you have questions.
        </p>
      )}

      {status === "found" && (
        <div className="mt-8">
          <p className="field-label mb-4">select your party</p>
          <div className="card-stack">
            {parties.map((p) => (
              <PartyCard key={p.id} party={p} onSelect={() => selectParty(p)} />
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
```

### Step 3 — Guest Count & Names

**`app/rsvp/guests/page.tsx`**
```tsx
"use client";
import { useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import StepLayout from "@/components/StepLayout";
import GuestStepper from "@/components/GuestStepper";

export default function GuestsPage() {
  const sp = useSearchParams();
  const router = useRouter();

  const partyId   = sp.get("partyId")   ?? "";
  const partyName = sp.get("partyName") ?? "";
  const maxGuests = Number(sp.get("maxGuests") ?? 1);
  const knownMembers = (sp.get("members") ?? "").split("||").filter(Boolean);

  const [guests, setGuests] = useState<string[]>([knownMembers[0] ?? ""]);

  function handleCountChange(count: number) {
    setGuests((prev) => {
      const next = [...prev];
      while (next.length < count) next.push(knownMembers[next.length] ?? "");
      return next.slice(0, count);
    });
  }

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    const params = new URLSearchParams({
      partyId,
      guests: guests.join("||"),
    });
    router.push(`/rsvp/meals?${params}`);
  }

  return (
    <StepLayout step={3} title="your party">
      <p className="body-text text-center mb-10">{partyName}</p>
      <form onSubmit={handleSubmit} className="form-stack">
        <div className="field-group">
          <label className="field-label">number of guests attending</label>
          <GuestStepper
            min={1}
            max={maxGuests}
            value={guests.length}
            onChange={handleCountChange}
          />
        </div>

        <div className="divider" />

        {guests.map((name, i) => (
          <div key={i} className="field-group">
            <label className="field-label">guest {i + 1}</label>
            <input
              type="text"
              value={name}
              onChange={(e) => {
                const next = [...guests];
                next[i] = e.target.value;
                setGuests(next);
              }}
              placeholder="full name"
              className="field-input"
              required
              autoComplete="off"
            />
          </div>
        ))}

        <button type="submit" className="btn-primary">
          continue to meal selection
        </button>
      </form>
    </StepLayout>
  );
}
```

### Step 4 — Meal Selection

**`app/rsvp/meals/page.tsx`**
```tsx
"use client";
import { useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import StepLayout from "@/components/StepLayout";
import MealCard from "@/components/MealCard";
import { MEAL_OPTIONS } from "@/lib/config";
import type { Meal } from "@/lib/types";

export default function MealsPage() {
  const sp = useSearchParams();
  const router = useRouter();

  const partyId = sp.get("partyId") ?? "";
  const guests  = (sp.get("guests") ?? "").split("||").filter(Boolean);

  const [selections, setSelections] = useState<Record<string, Meal>>({});

  const allSelected = guests.every((g) => selections[g]);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!allSelected) return;

    const res = await fetch("/api/rsvp", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        partyId: Number(partyId),
        guests: guests.map((g) => ({ guestName: g, meal: selections[g] })),
      }),
    });

    if (!res.ok) return; // TODO: surface error
    const { rsvpId } = await res.json();
    router.push(`/rsvp/confirm?rsvpId=${rsvpId}`);
  }

  return (
    <StepLayout step={4} title="dinner">
      <p className="body-text text-center mb-10">
        please select one option per guest
      </p>
      <form onSubmit={handleSubmit} className="form-stack">
        {guests.map((guest) => (
          <div key={guest} className="guest-meal-group">
            <p className="field-label mb-3">{guest}</p>
            <div className="meal-grid">
              {MEAL_OPTIONS.map((opt) => (
                <MealCard
                  key={opt.id}
                  option={opt}
                  selected={selections[guest] === opt.id}
                  onSelect={() => setSelections((s) => ({ ...s, [guest]: opt.id }))}
                />
              ))}
            </div>
          </div>
        ))}

        <button type="submit" className="btn-primary" disabled={!allSelected}>
          confirm rsvp
        </button>
      </form>
    </StepLayout>
  );
}
```

### Step 5 — Confirmation

**`app/rsvp/confirm/page.tsx`**
```tsx
import StepLayout from "@/components/StepLayout";
import CalendarButtons from "@/components/CalendarButtons";
import { WEDDING } from "@/lib/config";

export default function ConfirmPage({ searchParams }: { searchParams: { rsvpId?: string } }) {
  return (
    <StepLayout step={5} title="you're confirmed">
      <div className="text-center">
        <p className="display-italic mb-2">we can't wait to celebrate with you</p>
        <p className="body-text mb-1">{WEDDING.dateDisplay}</p>
        <p className="body-text mb-10">{WEDDING.location}</p>

        <div className="divider mb-10" />

        <p className="field-label mb-6">add to your calendar</p>
        <CalendarButtons rsvpId={searchParams.rsvpId ?? ""} />
      </div>
    </StepLayout>
  );
}
```

---

## 8. Shared Components

**`components/StepLayout.tsx`**
```tsx
import { WEDDING } from "@/lib/config";

const STEPS = ["find invitation", "your party", "guests", "dinner", "confirmed"];

export default function StepLayout({
  step,
  title,
  children,
}: {
  step: number;
  title: string;
  children: React.ReactNode;
}) {
  return (
    <div className="page-shell">
      <header className="page-header">
        <p className="eyebrow">{WEDDING.couple}</p>
        <h1 className="page-title">{title}</h1>
        <div className="step-dots">
          {STEPS.map((_, i) => (
            <span
              key={i}
              className={`step-dot ${i + 1 === step ? "active" : i + 1 < step ? "done" : ""}`}
            />
          ))}
        </div>
      </header>
      <main className="page-content">{children}</main>
    </div>
  );
}
```

**`components/MealCard.tsx`**
```tsx
type Props = {
  option: { id: string; label: string; description: string };
  selected: boolean;
  onSelect: () => void;
};

export default function MealCard({ option, selected, onSelect }: Props) {
  return (
    <button
      type="button"
      onClick={onSelect}
      className={`meal-card ${selected ? "meal-card--selected" : ""}`}
      aria-pressed={selected}
    >
      <span className="meal-card__label">{option.label}</span>
      <span className="meal-card__desc">{option.description}</span>
    </button>
  );
}
```

**`components/GuestStepper.tsx`**
```tsx
"use client";

type Props = {
  min: number;
  max: number;
  value: number;
  onChange: (n: number) => void;
};

export default function GuestStepper({ min, max, value, onChange }: Props) {
  return (
    <div className="stepper">
      <button
        type="button"
        className="stepper-btn"
        onClick={() => onChange(Math.max(min, value - 1))}
        disabled={value <= min}
        aria-label="Remove guest"
      >
        −
      </button>
      <span className="stepper-value">{value}</span>
      <button
        type="button"
        className="stepper-btn"
        onClick={() => onChange(Math.min(max, value + 1))}
        disabled={value >= max}
        aria-label="Add guest"
      >
        +
      </button>
    </div>
  );
}
```

**`components/CalendarButtons.tsx`**
```tsx
import { WEDDING } from "@/lib/config";

function buildGoogleLink() {
  const start = new Date(WEDDING.dateISO);
  const end = new Date(start.getTime() + 4 * 60 * 60 * 1000);
  const fmt = (d: Date) => d.toISOString().replace(/[-:]/g, "").split(".")[0] + "Z";
  return `https://calendar.google.com/calendar/render?action=TEMPLATE&text=${encodeURIComponent(
    WEDDING.couple + " Wedding"
  )}&dates=${fmt(start)}/${fmt(end)}&location=${encodeURIComponent(WEDDING.address)}`;
}

export default function CalendarButtons({ rsvpId }: { rsvpId: string }) {
  return (
    <div className="cal-buttons">
      <a
        href={`/api/calendar/${rsvpId}.ics`}
        className="btn-secondary"
        download
      >
        Apple / Outlook Calendar
      </a>
      <a
        href={buildGoogleLink()}
        target="_blank"
        rel="noopener noreferrer"
        className="btn-secondary"
      >
        Google Calendar
      </a>
    </div>
  );
}
```

---

## 9. Design System & Global Styles

**`app/globals.css`**
```css
/* ─── Tokens ─────────────────────────────────────── */
:root {
  --ivory:       #F5F0E8;
  --surface:     #FDFAF5;
  --ink:         #1C1C1C;
  --ink-muted:   #6B6560;
  --ink-faint:   #D4CFC8;
  --font-display: var(--font-display);   /* Cormorant Garamond */
  --font-body:    var(--font-body);      /* Jost */
  --ease:         cubic-bezier(0.25, 0, 0, 1);
  --radius:       4px;
}

/* ─── Reset ──────────────────────────────────────── */
*, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }
html { font-size: 16px; -webkit-text-size-adjust: 100%; }
body {
  background: var(--ivory);
  color: var(--ink);
  font-family: var(--font-body), system-ui, sans-serif;
  font-weight: 300;
  line-height: 1.6;
  min-height: 100dvh;
}
input, button, select { font: inherit; }

/* ─── Layout ─────────────────────────────────────── */
.page-shell {
  min-height: 100dvh;
  max-width: 440px;
  margin: 0 auto;
  padding: 3rem 1.5rem 4rem;
  display: flex;
  flex-direction: column;
}
.page-header {
  text-align: center;
  margin-bottom: 3rem;
}
.page-content { flex: 1; }

/* ─── Typography ─────────────────────────────────── */
.eyebrow {
  font-family: var(--font-body);
  font-size: 0.65rem;
  font-weight: 400;
  letter-spacing: 0.2em;
  text-transform: uppercase;
  color: var(--ink-muted);
  margin-bottom: 0.75rem;
}
.page-title {
  font-family: var(--font-display);
  font-size: clamp(2rem, 8vw, 2.75rem);
  font-weight: 300;
  letter-spacing: 0.15em;
  line-height: 1.1;
  margin-bottom: 1.5rem;
}
.display-italic {
  font-family: var(--font-display);
  font-size: 1.4rem;
  font-style: italic;
  font-weight: 300;
  color: var(--ink-muted);
  line-height: 1.4;
}
.body-text {
  font-family: var(--font-body);
  font-size: 0.875rem;
  font-weight: 300;
  letter-spacing: 0.05em;
  color: var(--ink-muted);
  line-height: 1.7;
}
.field-label {
  display: block;
  font-family: var(--font-body);
  font-size: 0.6rem;
  font-weight: 400;
  letter-spacing: 0.2em;
  text-transform: uppercase;
  color: var(--ink-muted);
}

/* ─── Step Dots ──────────────────────────────────── */
.step-dots {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
}
.step-dot {
  width: 5px; height: 5px;
  border-radius: 50%;
  background: var(--ink-faint);
  transition: background 0.3s var(--ease), transform 0.3s var(--ease);
}
.step-dot.active  { background: var(--ink); transform: scale(1.3); }
.step-dot.done    { background: var(--ink-muted); }

/* ─── Forms ──────────────────────────────────────── */
.form-stack { display: flex; flex-direction: column; gap: 1.75rem; }
.field-group { display: flex; flex-direction: column; gap: 0.5rem; }

.field-input {
  width: 100%;
  padding: 0.875rem 1rem;
  background: var(--surface);
  border: 1px solid var(--ink-faint);
  border-radius: var(--radius);
  font-family: var(--font-body);
  font-size: 1rem;        /* prevents iOS zoom */
  font-weight: 300;
  color: var(--ink);
  letter-spacing: 0.02em;
  outline: none;
  transition: border-color 0.2s var(--ease);
  -webkit-appearance: none;
}
.field-input::placeholder { color: var(--ink-faint); }
.field-input:focus { border-color: var(--ink); }

/* ─── Buttons ────────────────────────────────────── */
.btn-primary {
  width: 100%;
  padding: 1rem 1.5rem;
  background: var(--ink);
  color: var(--ivory);
  border: none;
  border-radius: var(--radius);
  font-family: var(--font-body);
  font-size: 0.7rem;
  font-weight: 400;
  letter-spacing: 0.2em;
  text-transform: uppercase;
  cursor: pointer;
  min-height: 54px;
  transition: opacity 0.2s var(--ease);
}
.btn-primary:hover:not(:disabled) { opacity: 0.8; }
.btn-primary:disabled { opacity: 0.35; cursor: not-allowed; }

.btn-secondary {
  display: block;
  width: 100%;
  padding: 0.875rem 1.5rem;
  background: transparent;
  color: var(--ink);
  border: 1px solid var(--ink-faint);
  border-radius: var(--radius);
  font-family: var(--font-body);
  font-size: 0.7rem;
  font-weight: 400;
  letter-spacing: 0.15em;
  text-transform: uppercase;
  text-align: center;
  text-decoration: none;
  cursor: pointer;
  min-height: 54px;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: border-color 0.2s var(--ease);
}
.btn-secondary:hover { border-color: var(--ink); }

/* ─── Cards ──────────────────────────────────────── */
.card-stack { display: flex; flex-direction: column; gap: 0.75rem; }

.party-card {
  padding: 1.25rem 1.5rem;
  background: var(--surface);
  border: 1px solid var(--ink-faint);
  border-radius: var(--radius);
  text-align: left;
  cursor: pointer;
  transition: border-color 0.2s var(--ease);
  width: 100%;
}
.party-card:hover { border-color: var(--ink); }
.party-card__name { font-family: var(--font-display); font-size: 1.3rem; font-weight: 400; }
.party-card__members { font-size: 0.8rem; color: var(--ink-muted); margin-top: 0.25rem; letter-spacing: 0.03em; }

/* ─── Meal Grid ──────────────────────────────────── */
.guest-meal-group { padding-bottom: 2rem; border-bottom: 1px solid var(--ink-faint); }
.guest-meal-group:last-of-type { border-bottom: none; }
.meal-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 0.625rem;
}
.meal-card {
  padding: 1rem;
  background: var(--surface);
  border: 1px solid var(--ink-faint);
  border-radius: var(--radius);
  text-align: left;
  cursor: pointer;
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
  transition: border-color 0.2s var(--ease);
  min-height: 80px;
}
.meal-card:hover { border-color: var(--ink-muted); }
.meal-card--selected { border-color: var(--ink); background: var(--ivory); }
.meal-card__label { font-family: var(--font-display); font-size: 1.1rem; font-weight: 400; }
.meal-card__desc  { font-size: 0.72rem; color: var(--ink-muted); letter-spacing: 0.02em; }

/* ─── Stepper ────────────────────────────────────── */
.stepper {
  display: flex;
  align-items: center;
  gap: 1.5rem;
}
.stepper-btn {
  width: 48px; height: 48px;
  background: var(--surface);
  border: 1px solid var(--ink-faint);
  border-radius: 50%;
  font-size: 1.5rem;
  font-weight: 300;
  color: var(--ink);
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: border-color 0.2s var(--ease);
}
.stepper-btn:hover:not(:disabled) { border-color: var(--ink); }
.stepper-btn:disabled { opacity: 0.3; cursor: not-allowed; }
.stepper-value {
  font-family: var(--font-display);
  font-size: 2.5rem;
  font-weight: 300;
  min-width: 2ch;
  text-align: center;
  line-height: 1;
}

/* ─── Calendar Buttons ───────────────────────────── */
.cal-buttons { display: flex; flex-direction: column; gap: 0.75rem; }

/* ─── Utilities ──────────────────────────────────── */
.divider { width: 40px; height: 1px; background: var(--ink-faint); margin: 0 auto; }
.status-message {
  font-family: var(--font-body);
  font-size: 0.82rem;
  letter-spacing: 0.04em;
  color: var(--ink-muted);
  text-align: center;
  line-height: 1.6;
}
```

---

## 10. Hosting — Vercel

```bash
# Install CLI
npm i -g vercel

# Link project
vercel login
vercel link

# Add environment variables (one by one, or via dashboard)
vercel env add DATABASE_URL
vercel env add DATABASE_AUTH_TOKEN
vercel env add ADMIN_PASSWORD
vercel env add WEDDING_DATE_ISO
vercel env add RSVP_DEADLINE_ISO

# Deploy
vercel --prod
```

**`next.config.ts`**
```typescript
import type { NextConfig } from "next";

const config: NextConfig = {
  experimental: {},
  // Security headers
  async headers() {
    return [
      {
        source: "/(.*)",
        headers: [
          { key: "X-Frame-Options",        value: "DENY" },
          { key: "X-Content-Type-Options", value: "nosniff" },
          { key: "Referrer-Policy",         value: "strict-origin-when-cross-origin" },
        ],
      },
    ];
  },
};

export default config;
```

**Custom domain** → Vercel Dashboard → Settings → Domains → Add `yourdomain.com`. Vercel handles HTTPS automatically.

---

## 11. Admin Dashboard

**`app/admin/page.tsx`**
```tsx
import { cookies } from "next/headers";
import { redirect } from "next/navigation";
import { getMealTotals, getAllRsvps, getPendingParties } from "@/lib/db";

export default async function AdminPage({
  searchParams,
}: {
  searchParams: { pw?: string };
}) {
  if (searchParams.pw !== process.env.ADMIN_PASSWORD) {
    redirect("/admin?pw=");  // Show form instead in a real app
  }

  const [totals, rsvps, pending] = await Promise.all([
    getMealTotals(),
    getAllRsvps(),
    getPendingParties(),
  ]);

  const totalGuests = rsvps.reduce((s, r) => s + r.guestCount, 0);

  return (
    <div style={{ fontFamily: "monospace", padding: "2rem", maxWidth: 700 }}>
      <h1>RSVP Summary</h1>
      <p>{rsvps.length} parties confirmed · {totalGuests} total guests</p>
      <h2>Meal Counts</h2>
      <pre>{JSON.stringify(totals, null, 2)}</pre>
      <h2>Pending ({pending.length})</h2>
      <ul>{pending.map((n) => <li key={n}>{n}</li>)}</ul>
      <p><a href={`/api/admin/export`}>Download CSV</a></p>
    </div>
  );
}
```

---

## 12. QR Code Generation

```bash
npm install qrcode @types/qrcode
```

```typescript
// scripts/generate-qr.ts
import QRCode from "qrcode";
import fs from "fs";
import path from "path";
import { parse } from "csv-parse/sync";

const BASE_URL = process.env.NEXT_PUBLIC_BASE_URL ?? "http://localhost:3000";
const OUT_DIR = "qr_codes";

fs.mkdirSync(OUT_DIR, { recursive: true });

const csv = fs.readFileSync("invitees.csv", "utf8");
const rows = parse(csv, { columns: true }) as Array<{
  party_name: string;
  invite_code: string;
}>;

const codes = [...new Set(rows.map((r) => r.invite_code))];
for (const code of codes) {
  const party = rows.find((r) => r.invite_code === code)!.party_name;
  const url   = `${BASE_URL}/rsvp?ref=${code}`;
  const file  = path.join(OUT_DIR, `${party.replace(/\s+/g, "_")}.png`);
  await QRCode.toFile(file, url, {
    errorCorrectionLevel: "H",
    margin: 2,
    width: 400,
    color: { dark: "#1C1C1C", light: "#F5F0E8" },  // matches invitation palette
  });
  console.log(`✓ ${party} → ${url}`);
}
```

```bash
npx ts-node scripts/generate-qr.ts
```

---

## 13. Calendar Integration

**`lib/calendar.ts`**
```typescript
import { createEvents, EventAttributes } from "ics";
import { WEDDING } from "./config";

export function generateIcs(): string {
  const start = new Date(WEDDING.dateISO);
  const end   = new Date(start.getTime() + 4 * 60 * 60 * 1000);

  const toArr = (d: Date): [number,number,number,number,number] =>
    [d.getFullYear(), d.getMonth()+1, d.getDate(), d.getHours(), d.getMinutes()];

  const event: EventAttributes = {
    start:       toArr(start),
    end:         toArr(end),
    title:       `${WEDDING.couple} Wedding`,
    location:    WEDDING.address,
    description: `We can't wait to celebrate with you!`,
    status:      "CONFIRMED",
    busyStatus:  "BUSY",
  };

  const { error, value } = createEvents([event]);
  if (error || !value) throw new Error("ICS generation failed");
  return value;
}
```

---

## 14. Testing with Playwright

**`playwright.config.ts`**
```typescript
import { defineConfig, devices } from "@playwright/test";

export default defineConfig({
  testDir: "./tests",
  fullyParallel: true,
  retries: process.env.CI ? 2 : 0,
  reporter: "html",
  use: {
    baseURL: "http://localhost:3000",
    trace: "on-first-retry",
    screenshot: "only-on-failure",
    // Simulate iPhone 14 — the primary device
    ...devices["iPhone 14"],
  },
  projects: [
    { name: "mobile-chrome", use: { ...devices["Pixel 7"] } },
    { name: "mobile-safari", use: { ...devices["iPhone 14"] } },
  ],
  webServer: {
    command: "npm run dev",
    url: "http://localhost:3000",
    reuseExistingServer: !process.env.CI,
  },
});
```

**`tests/rsvp-flow.spec.ts`** — Full E2E happy path
```typescript
import { test, expect } from "@playwright/test";

// These must exist in your test database
const KNOWN_NAME    = "Alice Johnson";
const PARTY_NAME    = "The Johnson Family";

test.describe("RSVP happy path", () => {
  test("completes full flow from landing to confirmation", async ({ page }) => {
    // Step 1 — Landing
    await page.goto("/rsvp");
    await expect(page.getByText("R S V P")).toBeVisible();

    // Search for name
    await page.getByPlaceholder("as written on your invitation").fill(KNOWN_NAME);
    await page.getByRole("button", { name: /find my invitation/i }).click();

    // Step 2 — Party selection
    await expect(page.getByText(PARTY_NAME)).toBeVisible();
    await page.getByText(PARTY_NAME).click();

    // Step 3 — Guests
    await expect(page).toHaveURL(/\/rsvp\/guests/);
    // Increase guest count to 2
    await page.getByLabel("Add guest").click();
    // Fill second guest name
    const inputs = page.getByRole("textbox");
    await inputs.nth(1).fill("Bob Johnson");
    await page.getByRole("button", { name: /continue/i }).click();

    // Step 4 — Meals
    await expect(page).toHaveURL(/\/rsvp\/meals/);
    // Select meal for each guest
    await page.getByRole("button", { name: "Steak" }).first().click();
    await page.getByRole("button", { name: "Fish"  }).nth(1).click();

    // Confirm is enabled now
    const confirmBtn = page.getByRole("button", { name: /confirm rsvp/i });
    await expect(confirmBtn).toBeEnabled();
    await confirmBtn.click();

    // Step 5 — Confirmation
    await expect(page).toHaveURL(/\/rsvp\/confirm/);
    await expect(page.getByText(/you're confirmed/i)).toBeVisible();
    await expect(page.getByText(/can't wait to celebrate/i)).toBeVisible();
    await expect(page.getByText("Apple / Outlook Calendar")).toBeVisible();
    await expect(page.getByText("Google Calendar")).toBeVisible();
  });
});
```

**`tests/validation.spec.ts`** — Edge cases
```typescript
import { test, expect } from "@playwright/test";

test.describe("Validation & edge cases", () => {
  test("shows error for unknown name", async ({ page }) => {
    await page.goto("/rsvp");
    await page.getByPlaceholder("as written on your invitation").fill("ZZZZZUNKNOWN");
    await page.getByRole("button", { name: /find/i }).click();
    await expect(page.getByText(/couldn't find/i)).toBeVisible();
  });

  test("confirm button is disabled until all meals selected", async ({ page }) => {
    await page.goto("/rsvp/meals?partyId=1&guests=Alice||Bob");
    const btn = page.getByRole("button", { name: /confirm rsvp/i });
    await expect(btn).toBeDisabled();
    await page.getByRole("button", { name: "Steak" }).first().click();
    // Still disabled — Bob hasn't chosen
    await expect(btn).toBeDisabled();
    await page.getByRole("button", { name: "Fish" }).nth(1).click();
    await expect(btn).toBeEnabled();
  });

  test("guest stepper respects min=1 and max from party", async ({ page }) => {
    await page.goto("/rsvp/guests?partyId=1&partyName=Test&maxGuests=2&members=Alice");
    const minus = page.getByLabel("Remove guest");
    const plus  = page.getByLabel("Add guest");
    await expect(minus).toBeDisabled();    // already at min=1
    await plus.click();
    await expect(plus).toBeDisabled();     // now at max=2
  });

  test("name input requires at least 2 characters", async ({ page }) => {
    await page.goto("/rsvp");
    await page.getByPlaceholder("as written on your invitation").fill("A");
    await page.getByRole("button", { name: /find/i }).click();
    // Browser native validation prevents submission
    const input = page.getByPlaceholder("as written on your invitation");
    await expect(input).toBeFocused();
  });
});
```

**`tests/admin.spec.ts`**
```typescript
import { test, expect } from "@playwright/test";

test.describe("Admin protection", () => {
  test("redirects without password", async ({ page }) => {
    await page.goto("/admin");
    // Should show empty password state, not data
    await expect(page.getByText("RSVP Summary")).not.toBeVisible();
  });

  test("export CSV requires auth header", async ({ request }) => {
    const res = await request.get("/api/admin/export");
    expect(res.status()).toBe(401);
  });
});
```

**Running tests:**
```bash
# Run all tests
npx playwright test

# Run with UI (great for debugging)
npx playwright test --ui

# Run only on iPhone simulator
npx playwright test --project=mobile-safari

# View HTML report
npx playwright show-report
```

---

## 15. Seeding Invitees from CSV

**`invitees.csv`** format:
```csv
party_name,member_name,max_guests,invite_code
"The Johnson Family","Alice Johnson",4,JOH001
"The Johnson Family","Bob Johnson",4,JOH001
"Maria Garcia","Maria Garcia",2,GAR002
"The Chen Party","Wei Chen",3,CHE003
"The Chen Party","Lin Chen",3,CHE003
```

**`scripts/seed.ts`**
```typescript
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
```

```bash
npx ts-node --esm scripts/seed.ts
```

---

## 16. Go-Live Checklist

```
Infrastructure
  □ Turso database created, schema applied
  □ All env vars added to Vercel
  □ Custom domain configured, HTTPS active
  □ RSVP_DEADLINE_ISO set correctly

Content
  □ invitees.csv finalized and seeded
  □ QR codes generated (npx ts-node scripts/generate-qr.ts)
  □ QR codes printed and included in physical invitations
  □ Wedding details correct (date, location, couple names)

Testing
  □ Full Playwright suite passes: npx playwright test
  □ Tested on real iPhone (Safari)
  □ Tested on real Android (Chrome)
  □ Tried an unknown name — error shows correctly
  □ Tried duplicate RSVP — updates cleanly
  □ Calendar .ics opens correctly in Apple Calendar
  □ Google Calendar link creates event correctly

Admin
  □ /admin?pw=... shows correct summary
  □ CSV export downloads with all meals
  □ Shared CSV export link with caterer

Post-deadline
  □ RSVP_DEADLINE_ISO has passed → form shows closed message
  □ Download final caterer CSV
```

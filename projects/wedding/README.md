# Wedding RSVP

A production-ready wedding RSVP application built with Next.js 15, TypeScript, Turso (libSQL), and deployed on Vercel. Guests look up their invitation by name, select attendees from their party, choose meal preferences per guest, and receive a confirmation with calendar add links.

---

## Design System

Drawn from the physical invitation card — no gradients, no heavy shadows, no rounded corners larger than 4px. White space is the decoration.

| Token | Value | Usage |
|-------|-------|-------|
| `--ivory` | `#F5F0E8` | Page background |
| `--ink` | `#1C1C1C` | Primary text, borders |
| `--ink-muted` | `#6B6560` | Secondary text, placeholders |
| `--ink-faint` | `#D4CFC8` | Dividers, inactive states |
| `--surface` | `#FDFAF5` | Card backgrounds |
| Font — Display | `Cormorant Garamond` | Headings (serif) |
| Font — Body | `Jost` | Body, labels, inputs |
| Letter spacing | `0.12em` on uppercase | All caps labels, nav |
| Motion | `ease: [0.25, 0, 0, 1]` | Slow, intentional transitions |

---

## Architecture

### 5-Step RSVP Flow

| Step | Route | Description |
|------|-------|-------------|
| 1 | `/rsvp` | Name lookup — guest types their name, matching parties are returned |
| 2 | (inline) | Party selection — rendered in the lookup page after search results appear |
| 3 | `/rsvp/guests` | Guest count and name confirmation |
| 4 | `/rsvp/meals` | Per-guest meal selection (steak / fish / chicken / vegetarian) |
| 5 | `/rsvp/confirm` | Confirmation with calendar download links |

### Server vs Client Components

- **Server Components**: `app/layout.tsx`, `app/rsvp/page.tsx`, `app/rsvp/confirm/page.tsx`, `app/admin/page.tsx`, `components/StepLayout.tsx`, `components/CalendarButtons.tsx`, `components/MealCard.tsx`, `components/PartyCard.tsx`
- **Client Components** (`"use client"`): `app/rsvp/LookupForm.tsx`, `app/rsvp/guests/page.tsx`, `app/rsvp/meals/page.tsx`, `components/GuestStepper.tsx`

### URL-State Data Flow

Data passes between steps via URL search params (no global state, no cookies):

```
/rsvp/guests?partyId=1&partyName=The+Johnson+Family&maxGuests=4&members=Alice||Bob
/rsvp/meals?partyId=1&guests=Alice||Bob
/rsvp/confirm?rsvpId=42
```

This makes every step deep-linkable and back-button safe.

---

## Database Schema

Hosted on [Turso](https://turso.tech/) (libSQL / SQLite edge).

```sql
parties (id, name, max_guests, invite_code)
  -- One row per invited group (e.g. "The Johnson Family")

invitees (id, party_id, name)
  -- Individual named guests within a party; used for name search

rsvps (id, party_id, attending, created_at)
  -- One row per party; UNIQUE(party_id) enforces one submission
  -- DELETE + re-INSERT allows editing before deadline

meal_selections (id, rsvp_id, guest_name, meal)
  -- One row per attending guest with their meal choice
  -- meal CHECK: steak | fish | chicken | vegetarian
```

Indexes on `invitees.name` (COLLATE NOCASE), `parties.invite_code`, and `rsvps.party_id`.

---

## How to Run Locally

### 1. Turso Setup

```bash
brew install tursodatabase/tap/turso
turso auth login
turso db create wedding-rsvp
turso db show wedding-rsvp       # copy the URL
turso db tokens create wedding-rsvp  # copy the auth token

# Open the shell and paste the schema from wedding-rsvp.md §3
turso db shell wedding-rsvp
```

### 2. Environment Variables

Copy `.env.local` and fill in real values:

```bash
cp .env.local .env.local
# Edit:
#   DATABASE_URL=libsql://your-db-name.turso.io
#   DATABASE_AUTH_TOKEN=your-token-here
#   ADMIN_PASSWORD=a-strong-password
#   WEDDING_DATE_ISO=2025-09-20T16:00:00
#   RSVP_DEADLINE_ISO=2025-09-01T23:59:59
#   (and the NEXT_PUBLIC_* display values)
```

### 3. Install and Seed

```bash
npm install

# Prepare invitees.csv (see format in the file), then:
npm run seed
```

### 4. Run

```bash
npm run dev
# Open http://localhost:3000/rsvp
```

---

## How to Test

Tests use [Playwright](https://playwright.dev/) and target mobile viewports (Pixel 7, iPhone 14).

```bash
# Install browsers (first time)
npx playwright install chromium

# Run all tests (starts dev server automatically)
npx playwright test

# Interactive UI mode (great for debugging)
npx playwright test --ui

# Run only on iPhone Safari
npx playwright test --project=mobile-safari

# View HTML report
npx playwright show-report
```

### Test Files

| File | Coverage |
|------|----------|
| `tests/rsvp-flow.spec.ts` | Full E2E happy path: lookup → party → guests → meals → confirmation |
| `tests/validation.spec.ts` | Unknown name error, meal button disabled state, stepper min/max, name min-length |
| `tests/admin.spec.ts` | Admin page redirect without password, CSV export 401 without auth header |

> The E2E test requires `"Alice Johnson"` / `"The Johnson Family"` to exist in the test database. Run `npm run seed` with the provided `invitees.csv` to populate them.

---

## Deployment

### Vercel

```bash
npm i -g vercel
vercel login
vercel link

# Add secrets
vercel env add DATABASE_URL
vercel env add DATABASE_AUTH_TOKEN
vercel env add ADMIN_PASSWORD
vercel env add WEDDING_DATE_ISO
vercel env add RSVP_DEADLINE_ISO

vercel --prod
```

**Custom domain**: Vercel Dashboard → Settings → Domains → Add your domain. HTTPS is automatic.

### Admin Dashboard

Visit `/admin?pw=YOUR_ADMIN_PASSWORD` to see:
- Total confirmed parties and guest count
- Meal counts by type
- List of parties who have not yet responded

Download the caterer CSV: `GET /api/admin/export` with header `x-admin-password: YOUR_ADMIN_PASSWORD`

### QR Codes (optional)

```bash
npm install qrcode @types/qrcode
npx ts-node scripts/generate-qr.ts
# Outputs one PNG per party to ./qr_codes/
```

---

## Go-Live Checklist

- [ ] Turso database created, schema applied
- [ ] All env vars added to Vercel
- [ ] Custom domain configured, HTTPS active
- [ ] `RSVP_DEADLINE_ISO` set correctly
- [ ] `invitees.csv` finalized and seeded
- [ ] Full Playwright suite passes: `npx playwright test`
- [ ] Tested on real iPhone (Safari) and Android (Chrome)
- [ ] Calendar `.ics` opens correctly in Apple Calendar
- [ ] `/admin?pw=...` shows correct summary
- [ ] CSV export downloads with all meals

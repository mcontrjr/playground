"use client";
import { useState, useRef, useCallback } from "react";
import WeddingCountdown from "@/components/WeddingCountdown";
import type { Meal } from "@/lib/types";

const MEAL_OPTIONS: Meal[] = ["steak", "fish", "chicken", "vegetarian"];

interface StatData {
  confirmed: number;
  remaining: number;
  totalGuests: number;
}

interface MealRow {
  partyId: number;
  partyName: string;
  guestName: string;
  meal: Meal;
}

interface SearchResult {
  id: number;
  name: string;
  maxGuests: number;
  confirmed: boolean;
  uuid: string | null;
}

interface PartyMeals {
  party: { id: number; name: string; maxGuests: number };
  meals: Array<{ guestName: string; meal: Meal }> | null;
}

interface EditState {
  partyId: number;
  partyName: string;
  maxGuests: number;
  uuid: string | null;
  guests: Array<{ guestName: string; meal: Meal }>;
}

// Group meal rows by party for the grouped table view
function groupByParty(rows: MealRow[]) {
  const groups: Array<{ partyId: number; partyName: string; guests: Array<{ guestName: string; meal: Meal }> }> = [];
  const seen = new Map<number, number>(); // partyId → group index
  for (const row of rows) {
    if (!seen.has(row.partyId)) {
      seen.set(row.partyId, groups.length);
      groups.push({ partyId: row.partyId, partyName: row.partyName, guests: [] });
    }
    groups[seen.get(row.partyId)!].guests.push({ guestName: row.guestName, meal: row.meal });
  }
  return groups;
}

export default function AdminClient({
  stats,
  meals,
  weddingDateISO,
  adminPw,
}: {
  stats: StatData;
  meals: MealRow[];
  weddingDateISO: string;
  adminPw: string;
}) {
  const [query, setQuery] = useState("");
  const [results, setResults] = useState<SearchResult[]>([]);
  const [searching, setSearching] = useState(false);
  const [editState, setEditState] = useState<EditState | null>(null);
  const [saving, setSaving] = useState(false);
  const [saveMsg, setSaveMsg] = useState("");
  const [mealRows, setMealRows] = useState<MealRow[]>(meals);
  const [showUuids, setShowUuids] = useState(false);
  const [copiedUuid, setCopiedUuid] = useState(false);
  const debounceRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  const search = useCallback(
    (q: string) => {
      if (debounceRef.current) clearTimeout(debounceRef.current);
      if (!q.trim()) { setResults([]); return; }
      debounceRef.current = setTimeout(async () => {
        setSearching(true);
        try {
          const res = await fetch(`/api/admin/party/search?pw=${encodeURIComponent(adminPw)}&q=${encodeURIComponent(q)}`);
          if (res.ok) setResults(await res.json());
        } finally {
          setSearching(false);
        }
      }, 250);
    },
    [adminPw]
  );

  async function openEdit(partyId: number, partyName: string) {
    const res = await fetch(`/api/admin/party/${partyId}?pw=${encodeURIComponent(adminPw)}`);
    if (!res.ok) return;
    const data: PartyMeals & { party: { uuid?: string | null } } = await res.json();
    setEditState({
      partyId:   data.party.id,
      partyName: data.party.name,
      maxGuests: data.party.maxGuests,
      uuid:      data.party.uuid ?? null,
      guests:    data.meals ?? [],
    });
    setSaveMsg("");
    setCopiedUuid(false);
  }

  async function refreshMealTable() {
    try {
      const res = await fetch(`/api/admin/meals?pw=${encodeURIComponent(adminPw)}`);
      if (res.ok) setMealRows(await res.json());
    } catch {
      // silent
    }
  }

  async function handleSave() {
    if (!editState) return;
    setSaving(true);
    setSaveMsg("");
    try {
      const res = await fetch(`/api/admin/party/${editState.partyId}?pw=${encodeURIComponent(adminPw)}`, {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          maxGuests: editState.maxGuests,
          guests:    editState.guests,
        }),
      });
      if (res.ok) {
        setSaveMsg("saved.");
        await refreshMealTable();
        // Auto-close after brief delay so user sees "saved."
        setTimeout(() => {
          setEditState(null);
          setSaveMsg("");
        }, 1000);
      } else {
        setSaveMsg("error saving.");
      }
    } finally {
      setSaving(false);
    }
  }

  function updateGuest(i: number, field: "guestName" | "meal", value: string) {
    setEditState((s) => {
      if (!s) return s;
      const guests = [...s.guests];
      guests[i] = { ...guests[i], [field]: value };
      return { ...s, guests };
    });
  }

  function addGuest() {
    setEditState((s) => {
      if (!s) return s;
      const newGuests = [...s.guests, { guestName: "", meal: "chicken" as Meal }];
      // Auto-increment maxGuests if needed
      const newMax = newGuests.length > s.maxGuests ? newGuests.length : s.maxGuests;
      return { ...s, guests: newGuests, maxGuests: newMax };
    });
  }

  function removeGuest(i: number) {
    setEditState((s) => {
      if (!s) return s;
      return { ...s, guests: s.guests.filter((_, idx) => idx !== i) };
    });
  }

  function closeEdit() {
    setEditState(null);
    setSaveMsg("");
  }

  async function copyUuid(uuid: string) {
    await navigator.clipboard.writeText(uuid);
    setCopiedUuid(true);
    setTimeout(() => setCopiedUuid(false), 2000);
  }

  const partyGroups = groupByParty(mealRows);

  return (
    <>
      {/* Header */}
      <header className="admin-header">
        <div className="admin-header__countdown">
          <WeddingCountdown targetDateISO={weddingDateISO} compact />
        </div>
        <p className="admin-header__title">rsvp admin</p>
        <div className="admin-header__actions">
          <a href={`/api/admin/export?pw=${encodeURIComponent(adminPw)}`} className="admin-download-link">
            download csv
          </a>
        </div>
      </header>

      <div className="admin-body">
        {/* Stat Cards */}
        <div className="admin-stats">
          <div className="admin-stat">
            <p className="admin-stat__label">Parties Confirmed</p>
            <p className="admin-stat__value">{stats.confirmed}</p>
          </div>
          <div className="admin-stat">
            <p className="admin-stat__label">Parties Remaining</p>
            <p className="admin-stat__value">{stats.remaining}</p>
          </div>
          <div className="admin-stat admin-stat--accent">
            <p className="admin-stat__label">Total Guests</p>
            <p className="admin-stat__value">{stats.totalGuests}</p>
          </div>
        </div>

        {/* Party Search + Edit */}
        <div>
          <p className="admin-section-title">search & edit parties</p>
          <div className="admin-search-wrap">
            <input
              type="text"
              className="admin-search-input"
              placeholder="search by party name…"
              value={query}
              onChange={(e) => { setQuery(e.target.value); search(e.target.value); }}
              autoComplete="off"
            />
            {searching && <p className="admin-status">searching…</p>}
            {results.length > 0 && (
              <div className="admin-result-list">
                {results.map((r) => (
                  <button
                    key={r.id}
                    type="button"
                    className="admin-result-item"
                    onClick={() => openEdit(r.id, r.name)}
                  >
                    <span className="admin-result-item__name">{r.name}</span>
                    <span className={`admin-result-item__badge admin-result-item__badge--${r.confirmed ? "confirmed" : "pending"}`}>
                      {r.confirmed ? "confirmed" : "pending"}
                    </span>
                  </button>
                ))}
              </div>
            )}

            {editState && (
              <div className="admin-edit-panel">
                <div className="admin-edit-panel__header">
                  <p className="admin-edit-panel__title">{editState.partyName}</p>
                  <button
                    type="button"
                    className="admin-edit-panel__close"
                    onClick={closeEdit}
                    aria-label="Close edit panel"
                  >
                    ×
                  </button>
                </div>

                {editState.uuid && (
                  <div className="admin-uuid-row">
                    <span className="admin-uuid-label">uuid</span>
                    <span className="admin-uuid-value">{editState.uuid}</span>
                    <button
                      type="button"
                      className="admin-uuid-copy"
                      onClick={() => copyUuid(editState.uuid!)}
                    >
                      {copiedUuid ? "copied!" : "copy"}
                    </button>
                  </div>
                )}

                <div className="admin-edit-row">
                  <span className="admin-edit-label">max guests</span>
                  <input
                    type="number"
                    min={1}
                    max={20}
                    className="admin-edit-input"
                    style={{ maxWidth: 80 }}
                    value={editState.maxGuests}
                    onChange={(e) => setEditState((s) => s ? { ...s, maxGuests: Number(e.target.value) } : s)}
                  />
                </div>

                {editState.guests.map((g, i) => (
                  <div key={i} className="admin-edit-row">
                    <span className="admin-edit-label">guest {i + 1}</span>
                    <input
                      type="text"
                      className="admin-edit-input"
                      value={g.guestName}
                      placeholder="name"
                      onChange={(e) => updateGuest(i, "guestName", e.target.value)}
                    />
                    <select
                      className="admin-meal-select"
                      value={g.meal}
                      onChange={(e) => updateGuest(i, "meal", e.target.value)}
                    >
                      {MEAL_OPTIONS.map((m) => (
                        <option key={m} value={m}>{m}</option>
                      ))}
                    </select>
                    <button
                      type="button"
                      onClick={() => removeGuest(i)}
                      style={{
                        background: "transparent",
                        border: "1px solid var(--admin-border)",
                        borderRadius: "50%",
                        width: 28,
                        height: 28,
                        color: "var(--admin-muted)",
                        cursor: "pointer",
                        flexShrink: 0,
                        fontSize: "1rem",
                        lineHeight: 1,
                        display: "flex",
                        alignItems: "center",
                        justifyContent: "center",
                      }}
                      aria-label="Remove guest"
                    >
                      ×
                    </button>
                  </div>
                ))}

                <button
                  type="button"
                  className="admin-btn-cancel"
                  onClick={addGuest}
                  style={{ alignSelf: "flex-start" }}
                >
                  + add guest
                </button>

                {saveMsg && <p className="admin-status">{saveMsg}</p>}

                <div className="admin-edit-actions">
                  <button type="button" className="admin-btn-save" disabled={saving} onClick={handleSave}>
                    {saving ? "saving…" : "save changes"}
                  </button>
                  <button type="button" className="admin-btn-cancel" onClick={closeEdit}>
                    cancel
                  </button>
                </div>
              </div>
            )}
          </div>
        </div>

        {/* Meal Table */}
        <div>
          <div className="admin-section-header">
            <p className="admin-section-title">meal selections</p>
            <button
              type="button"
              className="admin-btn-cancel"
              onClick={() => setShowUuids((v) => !v)}
              style={{ fontSize: "0.7rem" }}
            >
              {showUuids ? "hide uuids" : "show uuids"}
            </button>
          </div>
          <div className="admin-table-wrap">
            <table className="admin-table">
              <thead>
                <tr>
                  <th>Party</th>
                  <th>Guest</th>
                  <th>Meal</th>
                  <th style={{ width: 60 }}></th>
                </tr>
              </thead>
              <tbody>
                {partyGroups.length === 0 && (
                  <tr><td colSpan={4} className="admin-status">no meal selections yet</td></tr>
                )}
                {partyGroups.map((group) => (
                  <>
                    <tr key={`party-${group.partyId}`} className="admin-party-row">
                      <td colSpan={showUuids ? 1 : 2} className="admin-party-row__name">
                        {group.partyName}
                      </td>
                      {showUuids && (
                        <td className="admin-party-row__uuid">
                          {/* UUID shown from mealRows — not stored there, just party name available */}
                          <span style={{ fontFamily: "monospace", fontSize: "0.65rem", opacity: 0.5 }}>
                            id:{group.partyId}
                          </span>
                        </td>
                      )}
                      <td></td>
                      <td>
                        <button
                          type="button"
                          className="admin-table-edit-btn"
                          onClick={() => openEdit(group.partyId, group.partyName)}
                        >
                          edit
                        </button>
                      </td>
                    </tr>
                    {group.guests.map((guest, gi) => (
                      <tr key={`guest-${group.partyId}-${gi}`} className="admin-guest-row">
                        <td></td>
                        <td className="admin-guest-row__name">{guest.guestName}</td>
                        <td>
                          <span className={`admin-meal-pill admin-meal-pill--${guest.meal}`}>{guest.meal}</span>
                        </td>
                        <td></td>
                      </tr>
                    ))}
                  </>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </>
  );
}

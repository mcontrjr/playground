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

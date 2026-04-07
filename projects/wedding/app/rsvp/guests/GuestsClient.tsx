"use client";
import { useState } from "react";
import { useRouter } from "next/navigation";
import StepLayout from "@/components/StepLayout";
import GuestStepper from "@/components/GuestStepper";
import type { Party } from "@/lib/types";

export default function GuestsClient({ party }: { party: Party }) {
  const router = useRouter();
  const { uuid, name, maxGuests, members } = party;

  const [guests, setGuests] = useState<string[]>(
    members.length > 0 ? [...members] : [""]
  );

  function handleCountChange(count: number) {
    setGuests((prev) => {
      const next = [...prev];
      // When adding slots beyond known members, leave them blank
      while (next.length < count) next.push("");
      return next.slice(0, count);
    });
  }

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    const params = new URLSearchParams({
      uuid: uuid!,
      guests: guests.join("||"),
    });
    router.push(`/rsvp/meals?${params}`);
  }

  return (
    <StepLayout step={3} title="your party">
      <p className="body-text text-center mb-10">{name}</p>
      <form onSubmit={handleSubmit} className="form-stack">
        <div className="field-group" style={{ alignItems: "center", textAlign: "center" }}>
          <label className="field-label" style={{ textAlign: "center", width: "100%" }}>
            number of guests attending
          </label>
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
            <div style={{ display: "flex", gap: "0.5rem", alignItems: "center" }}>
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
              {guests.length > 1 && (
                <button
                  type="button"
                  aria-label={`Remove guest ${i + 1}`}
                  onClick={() => setGuests((prev) => prev.filter((_, idx) => idx !== i))}
                  style={{
                    flexShrink: 0,
                    width: 32,
                    height: 32,
                    background: "transparent",
                    border: "1px solid var(--ink-faint)",
                    borderRadius: "50%",
                    color: "var(--ink-muted)",
                    fontSize: "1rem",
                    lineHeight: 1,
                    cursor: "pointer",
                    display: "flex",
                    alignItems: "center",
                    justifyContent: "center",
                    transition: "border-color 0.2s var(--ease), color 0.2s var(--ease)",
                  }}
                  onMouseEnter={(e) => {
                    (e.currentTarget as HTMLButtonElement).style.borderColor = "var(--ink)";
                    (e.currentTarget as HTMLButtonElement).style.color = "var(--ink)";
                  }}
                  onMouseLeave={(e) => {
                    (e.currentTarget as HTMLButtonElement).style.borderColor = "var(--ink-faint)";
                    (e.currentTarget as HTMLButtonElement).style.color = "var(--ink-muted)";
                  }}
                >
                  ×
                </button>
              )}
            </div>
          </div>
        ))}

        <button type="submit" className="btn-primary">
          continue to meal selection
        </button>
      </form>
    </StepLayout>
  );
}

"use client";
import { useState } from "react";
import { useRouter } from "next/navigation";
import StepLayout from "@/components/StepLayout";
import MealCard from "@/components/MealCard";
import { MEAL_OPTIONS } from "@/lib/config";
import type { Meal } from "@/lib/types";

export default function MealsClient({ uuid, guests }: { uuid: string; guests: string[] }) {
  const router = useRouter();

  const [selections, setSelections] = useState<Record<string, Meal>>({});
  const [confirming, setConfirming] = useState(false);
  const [submitting, setSubmitting] = useState(false);

  const allSelected = guests.every((g) => selections[g]);

  async function handleConfirm() {
    if (!allSelected) return;
    setSubmitting(true);
    const res = await fetch("/api/rsvp", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        partyUuid: uuid,
        guests: guests.map((g) => ({ guestName: g, meal: selections[g] })),
      }),
    });
    if (!res.ok) { setSubmitting(false); return; }
    const { rsvpId } = await res.json();
    router.push(`/rsvp/confirm?rsvpId=${rsvpId}`);
  }

  return (
    <StepLayout step={4} title="dinner">
      <p className="body-text text-center mb-10">
        please select one option per guest
      </p>
      <div className="form-stack">
        {guests.map((guest) => (
          <div key={guest} className="guest-meal-group">
            <p className="field-label mb-3">{guest}</p>
            <div className="meal-grid">
              {MEAL_OPTIONS.map((opt) => (
                <MealCard
                  key={opt.id}
                  option={opt}
                  selected={selections[guest] === opt.id}
                  onSelect={() => {
                    setSelections((s) => ({ ...s, [guest]: opt.id }));
                    setConfirming(false);
                  }}
                />
              ))}
            </div>
          </div>
        ))}

        {!confirming ? (
          <button
            type="button"
            className="btn-danger"
            disabled={!allSelected}
            onClick={() => setConfirming(true)}
          >
            confirm rsvp
          </button>
        ) : (
          <div className="form-stack" style={{ gap: "0.75rem" }}>
            <p className="status-message">are you sure? this will submit your rsvp.</p>
            <button
              type="button"
              className="btn-danger"
              disabled={submitting}
              onClick={handleConfirm}
            >
              {submitting ? "submitting…" : "yes, confirm"}
            </button>
            <button
              type="button"
              className="btn-secondary"
              onClick={() => setConfirming(false)}
            >
              go back
            </button>
          </div>
        )}
      </div>
    </StepLayout>
  );
}

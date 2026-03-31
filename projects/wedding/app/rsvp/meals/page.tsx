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

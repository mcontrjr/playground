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

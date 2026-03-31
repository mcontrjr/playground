import type { Meal } from "./types";

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

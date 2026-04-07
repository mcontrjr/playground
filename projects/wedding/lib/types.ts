export type Meal = "steak" | "fish" | "chicken" | "vegetarian";

export interface Party {
  id: number;
  name: string;
  maxGuests: number;
  inviteCode: string | null;
  uuid: string | null;
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

export interface RsvpPayloadByUuid {
  partyUuid: string;
  guests: GuestMeal[];
}

export interface RsvpSummary {
  id: number;
  partyName: string;
  guestCount: number;
  meals: GuestMeal[];
  createdAt: string;
}

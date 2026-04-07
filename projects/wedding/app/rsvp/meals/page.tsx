import Link from "next/link";
import StepLayout from "@/components/StepLayout";
import { getPartyByUuid } from "@/lib/db";
import MealsClient from "./MealsClient";

export default async function MealsPage({
  searchParams,
}: {
  searchParams: Promise<{ uuid?: string; guests?: string }>;
}) {
  const { uuid, guests: guestsParam } = await searchParams;

  if (!uuid) {
    return <NotFoundPage />;
  }

  const party = await getPartyByUuid(uuid);
  if (!party) {
    return <NotFoundPage />;
  }

  const guests = (guestsParam ?? "").split("||").filter(Boolean);
  if (guests.length === 0) {
    return <NotFoundPage />;
  }

  return <MealsClient uuid={uuid} guests={guests} />;
}

function NotFoundPage() {
  return (
    <StepLayout step={1} title="404">
      <p className="body-text text-center mb-10">Guest Not Found</p>
      <p className="body-text text-center mb-10" style={{ fontSize: "0.9rem", color: "var(--ink-muted)" }}>
        This invitation link is invalid or has expired.
      </p>
      <Link href="/" className="btn-primary" style={{ display: "block", textAlign: "center" }}>
        return home
      </Link>
    </StepLayout>
  );
}

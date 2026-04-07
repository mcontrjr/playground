import Link from "next/link";
import StepLayout from "@/components/StepLayout";
import { getPartyByUuid, hasRsvpdByUuid } from "@/lib/db";
import GuestsClient from "./GuestsClient";

export default async function GuestsPage({
  searchParams,
}: {
  searchParams: Promise<{ uuid?: string }>;
}) {
  const { uuid: rawUuid } = await searchParams;
  const uuid = rawUuid ?? "";

  if (!uuid) {
    return <NotFoundPage />;
  }

  const party = await getPartyByUuid(uuid);

  if (!party) {
    return <NotFoundPage />;
  }

  const alreadyRsvpd = await hasRsvpdByUuid(uuid);
  if (alreadyRsvpd) {
    return <AlreadyRsvpdPage />;
  }

  return <GuestsClient party={party} />;
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

function AlreadyRsvpdPage() {
  return (
    <StepLayout step={1} title="already confirmed">
      <p className="body-text text-center mb-6">
        Your RSVP has already been received.
      </p>
      <p className="body-text text-center mb-10" style={{ fontSize: "0.9rem", color: "var(--ink-muted)" }}>
        To make changes, please contact Martin Contreras at{" "}
        <a href="tel:6198048975" style={{ color: "inherit", textDecoration: "underline" }}>
          619-804-8975
        </a>
        .
      </p>
      <Link href="/" className="btn-secondary" style={{ display: "block", textAlign: "center" }}>
        return home
      </Link>
    </StepLayout>
  );
}

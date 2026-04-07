import StepLayout from "@/components/StepLayout";
import CalendarButtons from "@/components/CalendarButtons";
import WeddingCountdown from "@/components/WeddingCountdown";
import { WEDDING } from "@/lib/config";

export default function ConfirmPage({ searchParams }: { searchParams: { rsvpId?: string } }) {
  return (
    <StepLayout step={5} title="you're confirmed">
      <WeddingCountdown targetDateISO={WEDDING.dateISO} />

      <div className="divider mb-6" />

      <div className="invite-card mb-6">
        <p className="invite-card__couple mb-2">{WEDDING.couple}</p>
        <p className="invite-card__honour">request the honour of your presence</p>
        <p className="invite-card__detail">{WEDDING.dateDisplay}</p>
        <p className="invite-card__detail">{WEDDING.location}</p>
      </div>

      <div className="divider mb-6" />

      <p className="field-label text-center mb-6">add to your calendar</p>
      <CalendarButtons rsvpId={searchParams.rsvpId ?? ""} />
    </StepLayout>
  );
}

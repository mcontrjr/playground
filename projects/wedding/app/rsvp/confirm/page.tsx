import StepLayout from "@/components/StepLayout";
import CalendarButtons from "@/components/CalendarButtons";
import { WEDDING } from "@/lib/config";

export default function ConfirmPage({ searchParams }: { searchParams: { rsvpId?: string } }) {
  return (
    <StepLayout step={5} title="you're confirmed">
      <div className="text-center">
        <p className="display-italic mb-2">we can't wait to celebrate with you</p>
        <p className="body-text mb-1">{WEDDING.dateDisplay}</p>
        <p className="body-text mb-10">{WEDDING.location}</p>

        <div className="divider mb-10" />

        <p className="field-label mb-6">add to your calendar</p>
        <CalendarButtons rsvpId={searchParams.rsvpId ?? ""} />
      </div>
    </StepLayout>
  );
}

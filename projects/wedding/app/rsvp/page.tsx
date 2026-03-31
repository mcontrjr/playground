import StepLayout from "@/components/StepLayout";
import LookupForm from "./LookupForm";
import { WEDDING } from "@/lib/config";

export default function RsvpPage({ searchParams }: { searchParams: { ref?: string } }) {
  return (
    <StepLayout step={1} title="R S V P">
      <p className="body-text text-center mb-10">
        kindly reply by {WEDDING.deadlineDisplay}
      </p>
      <LookupForm inviteRef={searchParams.ref} />
    </StepLayout>
  );
}

import type { Party } from "@/lib/types";

type Props = {
  party: Party;
  onSelect: () => void;
};

export default function PartyCard({ party, onSelect }: Props) {
  return (
    <button type="button" className="party-card" onClick={onSelect}>
      <p className="party-card__name">{party.name}</p>
      {party.members.length > 0 && (
        <p className="party-card__members">{party.members.join(", ")}</p>
      )}
    </button>
  );
}

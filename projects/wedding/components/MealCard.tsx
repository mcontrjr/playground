type Props = {
  option: { id: string; label: string; description: string };
  selected: boolean;
  onSelect: () => void;
};

export default function MealCard({ option, selected, onSelect }: Props) {
  return (
    <button
      type="button"
      onClick={onSelect}
      className={`meal-card ${selected ? "meal-card--selected" : ""}`}
      aria-pressed={selected}
    >
      <span className="meal-card__label">{option.label}</span>
      <span className="meal-card__desc">{option.description}</span>
    </button>
  );
}

"use client";

type Props = {
  min: number;
  max: number;
  value: number;
  onChange: (n: number) => void;
};

export default function GuestStepper({ min, max, value, onChange }: Props) {
  return (
    <div className="stepper">
      <button
        type="button"
        className="stepper-btn"
        onClick={() => onChange(Math.max(min, value - 1))}
        disabled={value <= min}
        aria-label="Remove guest"
      >
        −
      </button>
      <span className="stepper-value">{value}</span>
      <button
        type="button"
        className="stepper-btn"
        onClick={() => onChange(Math.min(max, value + 1))}
        disabled={value >= max}
        aria-label="Add guest"
      >
        +
      </button>
    </div>
  );
}

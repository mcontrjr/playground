import { WEDDING } from "@/lib/config";

const STEPS = ["find invitation", "your party", "guests", "dinner", "confirmed"];

export default function StepLayout({
  step,
  title,
  children,
}: {
  step: number;
  title: string;
  children: React.ReactNode;
}) {
  return (
    <div className="page-shell">
      <header className="page-header">
        <p className="eyebrow">{WEDDING.couple}</p>
        <h1 className="page-title">{title}</h1>
        <div className="step-dots">
          {STEPS.map((_, i) => (
            <span
              key={i}
              className={`step-dot ${i + 1 === step ? "active" : i + 1 < step ? "done" : ""}`}
            />
          ))}
        </div>
      </header>
      <main className="page-content">{children}</main>
    </div>
  );
}

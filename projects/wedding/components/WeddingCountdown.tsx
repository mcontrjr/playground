"use client";
import { useEffect, useState } from "react";

function formatCountdown(ms: number): string {
  if (ms <= 0) return "00 Days 00:00:00";
  const totalSeconds = Math.floor(ms / 1000);
  const d = Math.floor(totalSeconds / 86400);
  const h = Math.floor((totalSeconds % 86400) / 3600);
  const m = Math.floor((totalSeconds % 3600) / 60);
  const s = totalSeconds % 60;
  const time = [h, m, s].map((n) => String(n).padStart(2, "0")).join(":");
  return `${String(d).padStart(2, "0")} Days ${time}`;
}

export default function WeddingCountdown({
  targetDateISO,
  compact = false,
}: {
  targetDateISO: string;
  compact?: boolean;
}) {
  const [display, setDisplay] = useState("-- Days --:--:--");

  useEffect(() => {
    const target = new Date(targetDateISO).getTime();

    function tick() {
      setDisplay(formatCountdown(target - Date.now()));
    }

    tick();
    const id = setInterval(tick, 1000);
    return () => clearInterval(id);
  }, [targetDateISO]);

  if (compact) {
    return <span>{display}</span>;
  }

  return (
    <div className="countdown-wrap mb-6">
      <p className="countdown-label">until the big day</p>
      <p className="countdown-digits">{display}</p>
    </div>
  );
}

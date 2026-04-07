import { WEDDING } from "@/lib/config";

function buildGoogleLink() {
  const start = new Date(WEDDING.dateISO);
  const end = new Date(start.getTime() + 4 * 60 * 60 * 1000);
  const fmt = (d: Date) => d.toISOString().replace(/[-:]/g, "").split(".")[0] + "Z";
  return `https://calendar.google.com/calendar/render?action=TEMPLATE&text=${encodeURIComponent(
    WEDDING.couple + " Wedding"
  )}&dates=${fmt(start)}/${fmt(end)}&location=${encodeURIComponent(WEDDING.address)}`;
}

export default function CalendarButtons({ rsvpId }: { rsvpId: string }) {
  return (
    <div className="cal-buttons">
      <a
        href={`/api/calendar/${rsvpId}.ics`}
        className="btn-secondary"
        download
        style={{ display: "flex", alignItems: "center", justifyContent: "center", gap: "0.5rem" }}
      >
        {/* eslint-disable-next-line @next/next/no-img-element */}
        <img src="/calendar-svgrepo-com.svg" width={18} height={18} alt="" aria-hidden="true" />
        Apple / Outlook Calendar
      </a>
      <a
        href={buildGoogleLink()}
        target="_blank"
        rel="noopener noreferrer"
        className="btn-secondary"
        style={{ display: "flex", alignItems: "center", justifyContent: "center", gap: "0.5rem" }}
      >
        {/* eslint-disable-next-line @next/next/no-img-element */}
        <img src="/google-calendar.svg" width={18} height={18} alt="" aria-hidden="true" />
        Google Calendar
      </a>
    </div>
  );
}

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
      >
        Apple / Outlook Calendar
      </a>
      <a
        href={buildGoogleLink()}
        target="_blank"
        rel="noopener noreferrer"
        className="btn-secondary"
      >
        Google Calendar
      </a>
    </div>
  );
}

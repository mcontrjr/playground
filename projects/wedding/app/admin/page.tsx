import { cookies } from "next/headers";
import { redirect } from "next/navigation";
import { getMealTotals, getAllRsvps, getPendingParties } from "@/lib/db";

export default async function AdminPage({
  searchParams,
}: {
  searchParams: { pw?: string };
}) {
  if (searchParams.pw !== process.env.ADMIN_PASSWORD) {
    redirect("/admin?pw=");  // Show form instead in a real app
  }

  const [totals, rsvps, pending] = await Promise.all([
    getMealTotals(),
    getAllRsvps(),
    getPendingParties(),
  ]);

  const totalGuests = rsvps.reduce((s, r) => s + r.guestCount, 0);

  return (
    <div style={{ fontFamily: "monospace", padding: "2rem", maxWidth: 700 }}>
      <h1>RSVP Summary</h1>
      <p>{rsvps.length} parties confirmed · {totalGuests} total guests</p>
      <h2>Meal Counts</h2>
      <pre>{JSON.stringify(totals, null, 2)}</pre>
      <h2>Pending ({pending.length})</h2>
      <ul>{pending.map((n) => <li key={n}>{n}</li>)}</ul>
      <p><a href={`/api/admin/export`}>Download CSV</a></p>
    </div>
  );
}

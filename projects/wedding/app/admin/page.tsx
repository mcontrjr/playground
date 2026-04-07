import { redirect } from "next/navigation";
import { getAdminStats, getMealTableRows } from "@/lib/db";
import { WEDDING } from "@/lib/config";
import AdminClient from "./AdminClient";
import "./admin.css";

export default async function AdminPage({
  searchParams,
}: {
  searchParams: { pw?: string };
}) {
  const pw = searchParams.pw ?? "";
  if (pw !== process.env.ADMIN_PASSWORD) {
    return (
      <div style={{
        minHeight: "100dvh",
        background: "#1C1C1C",
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        fontFamily: "system-ui",
        color: "#9A9590",
        fontSize: "0.75rem",
        letterSpacing: "0.15em",
        textTransform: "uppercase",
      }}>
        access denied
      </div>
    );
  }

  const [stats, meals] = await Promise.all([
    getAdminStats(),
    getMealTableRows(),
  ]);

  return (
    <div className="admin-shell">
      <AdminClient
        stats={stats}
        meals={meals}
        weddingDateISO={WEDDING.dateISO}
        adminPw={pw}
      />
    </div>
  );
}

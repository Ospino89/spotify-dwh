import { createFileRoute } from "@tanstack/react-router";
import { useEffect, useRef, useState } from "react";

export const Route = createFileRoute("/_authenticated/etl")({
  head: () => ({ meta: [{ title: "ETL — My Spotify Wrapped" }] }),
  component: EtlPage,
});

type Status = "loaded" | "stale" | "empty";

const tables: { name: string; records: number; lastSync: string; status: Status }[] = [
  { name: "dim_users", records: 1, lastSync: "2 min ago", status: "loaded" },
  { name: "dim_artists", records: 247, lastSync: "2 min ago", status: "loaded" },
  { name: "dim_tracks", records: 1842, lastSync: "3 hr ago", status: "stale" },
  { name: "fact_listening_history", records: 12483, lastSync: "2 min ago", status: "loaded" },
];

const history = [
  { date: "2025-05-15 14:22", duration: "12.4s", added: 47, status: "loaded" as Status },
  { date: "2025-05-14 09:11", duration: "11.8s", added: 32, status: "loaded" as Status },
  { date: "2025-05-13 18:46", duration: "13.2s", added: 58, status: "loaded" as Status },
  { date: "2025-05-12 21:03", duration: "0.4s", added: 0, status: "empty" as Status },
  { date: "2025-05-11 12:30", duration: "12.0s", added: 41, status: "loaded" as Status },
];

const statusStyles: Record<Status, string> = {
  loaded: "bg-primary/15 text-primary border border-primary/30",
  stale: "bg-yellow-500/15 text-yellow-400 border border-yellow-500/30",
  empty: "bg-red-500/15 text-red-400 border border-red-500/30",
};

function StatusBadge({ status }: { status: Status }) {
  return (
    <span className={`inline-flex rounded-full px-2.5 py-0.5 text-xs font-medium capitalize ${statusStyles[status]}`}>
      {status}
    </span>
  );
}

const syncSteps = [
  "→ Connecting to Spotify Web API...",
  "✓ Auth: token refreshed",
  "→ Extract: fetching top artists",
  "✓ Extract: 50 artists fetched",
  "→ Extract: fetching recently played",
  "✓ Extract: 200 plays fetched",
  "→ Transform: normalizing track metadata",
  "✓ Transform: 200 records normalized",
  "→ Load: upserting into fact_listening_history",
  "✓ Load: 47 new records inserted",
  "✓ Sync complete in 12.4s",
];

function EtlPage() {
  const [logs, setLogs] = useState<string[]>([]);
  const [running, setRunning] = useState(false);
  const logRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (logRef.current) logRef.current.scrollTop = logRef.current.scrollHeight;
  }, [logs]);

  const runSync = () => {
    if (running) return;
    setRunning(true);
    setLogs([]);
    syncSteps.forEach((step, i) => {
      setTimeout(() => {
        setLogs((prev) => [...prev, step]);
        if (i === syncSteps.length - 1) setRunning(false);
      }, i * 500);
    });
  };

  return (
    <>
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-foreground">ETL Pipeline</h1>
        <p className="mt-1 text-sm text-muted-foreground">
          Extract from Spotify, transform, and load into your warehouse.
        </p>
      </div>

      <section className="rounded-2xl border border-border bg-card p-6">
        <h2 className="text-sm font-semibold uppercase tracking-wider text-muted-foreground">
          Data Warehouse Status
        </h2>
        <div className="mt-5 overflow-hidden rounded-lg border border-border">
          <table className="w-full text-sm">
            <thead className="bg-secondary/50 text-left text-xs uppercase tracking-wider text-muted-foreground">
              <tr>
                <th className="px-4 py-3 font-medium">Table</th>
                <th className="px-4 py-3 font-medium">Records</th>
                <th className="px-4 py-3 font-medium">Last Sync</th>
                <th className="px-4 py-3 font-medium">Status</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-border">
              {tables.map((t) => (
                <tr key={t.name}>
                  <td className="px-4 py-3 font-mono text-foreground">{t.name}</td>
                  <td className="px-4 py-3 tabular-nums text-foreground">{t.records.toLocaleString()}</td>
                  <td className="px-4 py-3 text-muted-foreground">{t.lastSync}</td>
                  <td className="px-4 py-3"><StatusBadge status={t.status} /></td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>

      <section className="mt-8 rounded-2xl border border-border bg-card p-6">
        <h2 className="text-sm font-semibold uppercase tracking-wider text-muted-foreground">
          Sync Your Data
        </h2>
        <div className="mt-5">
          <button
            onClick={runSync}
            disabled={running}
            className="rounded-full bg-primary px-6 py-2.5 text-sm font-semibold text-primary-foreground transition-colors hover:bg-primary/90 disabled:cursor-not-allowed disabled:opacity-60"
          >
            {running ? "Syncing..." : "Sync Now"}
          </button>
        </div>
        <div
          ref={logRef}
          className="mt-5 h-64 overflow-y-auto rounded-lg border border-border bg-background p-4 font-mono text-xs leading-relaxed text-foreground/90"
        >
          {logs.length === 0 ? (
            <span className="text-muted-foreground">$ Awaiting sync. Click "Sync Now" to begin.</span>
          ) : (
            logs.map((line, i) => (
              <div key={i} className={line.startsWith("✓") ? "text-primary" : "text-foreground/80"}>
                {line}
              </div>
            ))
          )}
        </div>
      </section>

      <section className="mt-8 rounded-2xl border border-border bg-card p-6">
        <h2 className="text-sm font-semibold uppercase tracking-wider text-muted-foreground">
          Recent Runs
        </h2>
        <div className="mt-5 overflow-hidden rounded-lg border border-border">
          <table className="w-full text-sm">
            <thead className="bg-secondary/50 text-left text-xs uppercase tracking-wider text-muted-foreground">
              <tr>
                <th className="px-4 py-3 font-medium">Date</th>
                <th className="px-4 py-3 font-medium">Duration</th>
                <th className="px-4 py-3 font-medium">Records added</th>
                <th className="px-4 py-3 font-medium">Status</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-border">
              {history.map((h) => (
                <tr key={h.date}>
                  <td className="px-4 py-3 font-mono text-xs text-foreground">{h.date}</td>
                  <td className="px-4 py-3 tabular-nums text-foreground">{h.duration}</td>
                  <td className="px-4 py-3 tabular-nums text-foreground">{h.added}</td>
                  <td className="px-4 py-3"><StatusBadge status={h.status} /></td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>
    </>
  );
}

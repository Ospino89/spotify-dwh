import { useCallback, useEffect, useRef, useState } from "react";
import { Loader2 } from "lucide-react";
import { PageShell } from "@/components/Navbar";
import {
  formatDurationMs,
  getEtlStatus,
  getTopArtists,
  getTopTracks,
  getListeningHistory,
  runEtl,
} from "@/lib/services";
import type { EtlRun } from "@/types/etl";

type Status = "success" | "error" | "running" | "unknown";

function mapStatus(status: string): Status {
  if (status === "success") return "success";
  if (status === "error") return "error";
  if (status === "running") return "running";
  return "unknown";
}

const statusStyles: Record<Status, string> = {
  success: "bg-[#1DB954]/15 text-[#1DB954] border border-[#1DB954]/30",
  error: "bg-red-500/15 text-red-400 border border-red-500/30",
  running: "bg-yellow-500/15 text-yellow-400 border border-yellow-500/30",
  unknown: "bg-[#2A2A2A] text-[#888888] border border-[#2A2A2A]",
};

function StatusBadge({ status }: { status: Status }) {
  return (
    <span
      className={`inline-flex rounded-full px-2.5 py-0.5 text-xs font-medium capitalize ${statusStyles[status]}`}
    >
      {status}
    </span>
  );
}

export default function EtlPage() {
  const [runs, setRuns] = useState<EtlRun[]>([]);
  const [counts, setCounts] = useState({ artists: 0, tracks: 0, history: 0 });
  const [logs, setLogs] = useState<string[]>([]);
  const [running, setRunning] = useState(false);
  const [loading, setLoading] = useState(true);
  const logRef = useRef<HTMLDivElement>(null);

  const refresh = useCallback(async () => {
    setLoading(true);
    try {
      const [statusData, artists, tracks, history] = await Promise.all([
        getEtlStatus(),
        getTopArtists(50),
        getTopTracks(50),
        getListeningHistory(50),
      ]);
      setRuns(statusData);
      setCounts({
        artists: artists.length,
        tracks: tracks.length,
        history: history.length,
      });
    } catch (e) {
      setLogs((prev) => [
        ...prev,
        `✗ Error al cargar estado: ${e instanceof Error ? e.message : "desconocido"}`,
      ]);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    refresh();
  }, [refresh]);

  useEffect(() => {
    if (logRef.current) logRef.current.scrollTop = logRef.current.scrollHeight;
  }, [logs]);

  const runSync = async () => {
    if (running) return;
    setRunning(true);
    setLogs(["→ Iniciando pipeline ETL..."]);
    try {
      const result = await runEtl();
      setLogs((prev) => [
        ...prev,
        `✓ ETL ${result.status} en ${formatDurationMs(result.duration_ms)}`,
        `✓ Artistas: +${result.artists_inserted} / actualizados ${result.artists_skipped}`,
        `✓ Tracks: +${result.tracks_inserted} / actualizados ${result.tracks_skipped}`,
        `✓ Historial: +${result.history_inserted} omitidos ${result.history_skipped}`,
        ...(result.tracks_backfilled != null
          ? [`✓ Popularidad reparada: ${result.tracks_backfilled} tracks`]
          : []),
      ]);
      await refresh();
    } catch (e) {
      setLogs((prev) => [
        ...prev,
        `✗ ${e instanceof Error ? e.message : "Error en ETL"}`,
      ]);
    } finally {
      setRunning(false);
    }
  };

  const lastRun = runs[0];
  const tableRows = [
    { name: "dim_artists", records: counts.artists, ok: counts.artists > 0 },
    { name: "dim_tracks", records: counts.tracks, ok: counts.tracks > 0 },
    { name: "fact_listening_history", records: counts.history, ok: counts.history > 0 },
  ];

  return (
    <PageShell>
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-white">Pipeline ETL</h1>
        <p className="mt-1 text-sm text-[#888888]">
          Extrae de Spotify, transforma y carga en tu warehouse.
        </p>
      </div>

      {loading && (
        <div className="mb-6 flex items-center gap-2 text-sm text-[#888888]">
          <Loader2 className="h-4 w-4 animate-spin" />
          Cargando estado...
        </div>
      )}

      <section className="rounded-2xl border border-[#2A2A2A] bg-[#1A1A1A] p-6">
        <h2 className="text-sm font-semibold uppercase tracking-wider text-[#888888]">
          Estado del DWH
        </h2>
        <div className="mt-5 overflow-hidden rounded-lg border border-[#2A2A2A]">
          <table className="w-full text-sm">
            <thead className="bg-[#2A2A2A]/50 text-left text-xs uppercase tracking-wider text-[#888888]">
              <tr>
                <th className="px-4 py-3 font-medium">Tabla</th>
                <th className="px-4 py-3 font-medium">Registros (muestra API)</th>
                <th className="px-4 py-3 font-medium">Estado</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-[#2A2A2A]">
              {tableRows.map((t) => (
                <tr key={t.name}>
                  <td className="px-4 py-3 font-mono text-white">{t.name}</td>
                  <td className="px-4 py-3 tabular-nums text-white">{t.records}</td>
                  <td className="px-4 py-3">
                    <StatusBadge status={t.ok ? "success" : "unknown"} />
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>

      <section className="mt-8 rounded-2xl border border-[#2A2A2A] bg-[#1A1A1A] p-6">
        <h2 className="text-sm font-semibold uppercase tracking-wider text-[#888888]">
          Sincronizar datos
        </h2>
        <div className="mt-5">
          <button
            onClick={runSync}
            disabled={running}
            className="rounded-full bg-[#1DB954] px-6 py-2.5 text-sm font-semibold text-black transition-colors hover:bg-[#1aa34a] disabled:cursor-not-allowed disabled:opacity-60"
          >
            {running ? "Sincronizando..." : "Sync Now"}
          </button>
        </div>
        <div
          ref={logRef}
          className="mt-5 h-64 overflow-y-auto rounded-lg border border-[#2A2A2A] bg-[#0D0D0D] p-4 font-mono text-xs leading-relaxed"
        >
          {logs.length === 0 ? (
            <span className="text-[#888888]">$ Esperando sync. Pulsa &quot;Sync Now&quot;.</span>
          ) : (
            logs.map((line, i) => (
              <div key={i} className={line.startsWith("✓") ? "text-[#1DB954]" : "text-white/80"}>
                {line}
              </div>
            ))
          )}
        </div>
      </section>

      <section className="mt-8 rounded-2xl border border-[#2A2A2A] bg-[#1A1A1A] p-6">
        <h2 className="text-sm font-semibold uppercase tracking-wider text-[#888888]">
          Ejecuciones recientes
        </h2>
        <div className="mt-5 overflow-hidden rounded-lg border border-[#2A2A2A]">
          <table className="w-full text-sm">
            <thead className="bg-[#2A2A2A]/50 text-left text-xs uppercase tracking-wider text-[#888888]">
              <tr>
                <th className="px-4 py-3 font-medium">Fecha</th>
                <th className="px-4 py-3 font-medium">Duración</th>
                <th className="px-4 py-3 font-medium">Historial +</th>
                <th className="px-4 py-3 font-medium">Estado</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-[#2A2A2A]">
              {runs.length === 0 ? (
                <tr>
                  <td colSpan={4} className="px-4 py-6 text-center text-[#888888]">
                    Sin ejecuciones registradas
                  </td>
                </tr>
              ) : (
                runs.map((h) => (
                  <tr key={h.audit_id}>
                    <td className="px-4 py-3 font-mono text-xs text-white">
                      {new Date(h.started_at).toLocaleString("es-CO")}
                    </td>
                    <td className="px-4 py-3 tabular-nums text-white">
                      {formatDurationMs(h.duration_ms)}
                    </td>
                    <td className="px-4 py-3 tabular-nums text-white">
                      {h.history_inserted}
                    </td>
                    <td className="px-4 py-3">
                      <StatusBadge status={mapStatus(h.status)} />
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </section>
    </PageShell>
  );
}

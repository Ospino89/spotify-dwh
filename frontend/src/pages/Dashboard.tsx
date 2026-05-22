import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { Database, Loader2 } from "lucide-react";
import { PageShell } from "@/components/Navbar";
import {
  formatTrackDuration,
  getDominantGenres,
  getPlaysByHour,
  getTopArtists,
  getTopTracks,
} from "@/lib/services";
import type { Artist } from "@/types/artist";
import type { Track } from "@/types/track";

function Card({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <div className="rounded-2xl border border-[#2A2A2A] bg-[#1A1A1A] p-6">
      <h3 className="text-sm font-semibold uppercase tracking-wider text-[#888888]">{title}</h3>
      <div className="mt-5">{children}</div>
    </div>
  );
}

export default function DashboardPage() {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [artists, setArtists] = useState<Artist[]>([]);
  const [tracks, setTracks] = useState<Track[]>([]);
  const [hours, setHours] = useState<number[]>(Array(24).fill(0));
  const [genres, setGenres] = useState<{ name: string; plays: number }[]>([]);

  useEffect(() => {
    let cancelled = false;
    (async () => {
      setLoading(true);
      setError(null);
      try {
        const [artistsData, tracksData, hoursData, genresData] = await Promise.all([
          getTopArtists(10),
          getTopTracks(10),
          getPlaysByHour(),
          getDominantGenres(10),
        ]);
        if (cancelled) return;
        setArtists(artistsData);
        setTracks(tracksData);
        setHours(
          Array.isArray(hoursData) && hoursData.length === 24
            ? hoursData
            : Array(24).fill(0),
        );
        setGenres(Array.isArray(genresData) ? genresData : []);
      } catch (e) {
        if (!cancelled) setError(e instanceof Error ? e.message : "Error al cargar datos");
      } finally {
        if (!cancelled) setLoading(false);
      }
    })();
    return () => {
      cancelled = true;
    };
  }, []);

  const hasData = artists.length > 0 || tracks.length > 0;
  const peakIdx = hours.reduce(
    (best, v, i) => (v > hours[best] ? i : best),
    0,
  );
  const maxHour = Math.max(...hours, 1);
  const maxGenre = Math.max(...genres.map((g) => g.plays), 1);

  if (loading) {
    return (
      <PageShell>
        <div className="flex min-h-[50vh] items-center justify-center gap-3 text-[#888888]">
          <Loader2 className="h-6 w-6 animate-spin text-[#1DB954]" />
          Cargando tu wrapped...
        </div>
      </PageShell>
    );
  }

  if (error) {
    return (
      <PageShell>
        <div className="rounded-2xl border border-red-500/30 bg-red-500/10 p-6 text-red-300">
          {error}
        </div>
      </PageShell>
    );
  }

  if (!hasData) {
    return (
      <PageShell>
        <div className="flex min-h-[60vh] flex-col items-center justify-center text-center">
          <Database className="h-10 w-10 text-[#888888]" />
          <p className="mt-4 text-base text-white">
            Tu DWH está vacío. Ve a ETL y sincroniza tus datos.
          </p>
          <Link
            to="/etl"
            className="mt-6 rounded-full border border-[#1DB954] px-5 py-2 text-sm font-semibold text-[#1DB954] transition-colors hover:bg-[#1DB954] hover:text-black"
          >
            Ir a ETL
          </Link>
        </div>
      </PageShell>
    );
  }

  return (
    <PageShell>
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-white">Tu escucha, de un vistazo</h1>
        <p className="mt-1 text-sm text-[#888888]">Datos desde tu data warehouse</p>
      </div>

      <div className="grid gap-6 md:grid-cols-2">
        <Card title="Top artistas">
          <ul className="space-y-4">
            {artists.map((a, i) => {
              const barScore =
                a.popularity ??
                (a.followers_count
                  ? Math.min(100, Math.round(a.followers_count / 50_000))
                  : 0);
              return (
                <li key={a.spotify_id} className="flex items-center gap-4">
                  <span className="w-5 text-sm tabular-nums text-[#888888]">{i + 1}</span>
                  <div className="flex-1">
                    <div className="mb-1.5 flex items-center justify-between">
                      <span className="text-sm font-medium text-white">{a.name}</span>
                      <span className="text-xs tabular-nums text-[#888888]">
                        {a.popularity != null ? `pop ${a.popularity}` : `${a.followers_count ?? 0} seg.`}
                      </span>
                    </div>
                    <div className="h-1.5 w-full overflow-hidden rounded-full bg-[#2A2A2A]">
                      <div
                        className="h-full rounded-full bg-[#1DB954]"
                        style={{ width: `${barScore}%` }}
                      />
                    </div>
                    {a.genres?.length > 0 && (
                      <p className="mt-1 truncate text-xs text-[#666]">{a.genres.join(", ")}</p>
                    )}
                  </div>
                </li>
              );
            })}
          </ul>
        </Card>

        <Card title="Top tracks">
          <ul className="space-y-3">
            {tracks.map((t, i) => (
              <li key={t.spotify_id} className="flex items-center gap-4">
                <span className="w-5 text-sm tabular-nums text-[#888888]">{i + 1}</span>
                <div className="min-w-0 flex-1">
                  <div className="truncate text-sm font-medium text-white">{t.name}</div>
                  <div className="truncate text-xs text-[#888888]">{t.album_name ?? "—"}</div>
                </div>
                <span className="text-xs tabular-nums text-[#888888]">
                  {formatTrackDuration(t.duration_ms)}
                </span>
              </li>
            ))}
          </ul>
        </Card>

        <Card title="Hora pico">
          {Math.max(...hours) === 0 ? (
            <p className="text-sm text-[#888888]">Sin reproducciones en el historial cargado.</p>
          ) : (
            <>
              <div className="text-3xl font-bold tracking-tight text-white">
                {String(peakIdx).padStart(2, "0")}:00 – {String((peakIdx + 1) % 24).padStart(2, "0")}:00
              </div>
              <p className="mt-1 text-xs text-[#888888]">
                Hora con más reproducciones (todo tu historial en el DWH)
              </p>
              <div className="mt-6 flex h-24 items-end gap-1">
                {hours.map((v, i) => (
                  <div
                    key={i}
                    className={`flex-1 rounded-sm ${i === peakIdx ? "bg-[#1DB954]" : "bg-[#2A2A2A]"}`}
                    style={{ height: `${(v / maxHour) * 100}%`, minHeight: v > 0 ? "4px" : "0" }}
                    title={`${i}:00 — ${v} plays`}
                  />
                ))}
              </div>
              <div className="mt-2 flex justify-between text-[10px] text-[#888888]">
                <span>00</span>
                <span>06</span>
                <span>12</span>
                <span>18</span>
                <span>23</span>
              </div>
            </>
          )}
        </Card>

        <Card title="Géneros dominantes">
          {genres.length === 0 ? (
            <p className="text-sm text-[#888888]">
              Sin géneros en artistas o historial vacío. Ejecuta el ETL de nuevo.
            </p>
          ) : (
            <ul className="space-y-4">
              {genres.map((g) => (
                <li key={g.name}>
                  <div className="mb-1.5 flex items-center justify-between">
                    <span className="text-sm font-medium text-white">{g.name}</span>
                    <span className="text-xs tabular-nums text-[#888888]">
                      {g.plays} plays
                    </span>
                  </div>
                  <div className="h-2 w-full overflow-hidden rounded-full bg-[#2A2A2A]">
                    <div
                      className="h-full rounded-full bg-[#1DB954]"
                      style={{ width: `${(g.plays / maxGenre) * 100}%` }}
                    />
                  </div>
                </li>
              ))}
            </ul>
          )}
        </Card>
      </div>
    </PageShell>
  );
}

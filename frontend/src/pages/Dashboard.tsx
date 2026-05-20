import { useState } from "react";
import { Link } from "react-router-dom";
import { Database } from "lucide-react";
import { PageShell } from "@/components/Navbar";

const topArtists = [
  { name: "Tame Impala", popularity: 92 },
  { name: "Arctic Monkeys", popularity: 88 },
  { name: "Phoebe Bridgers", popularity: 76 },
  { name: "Mac DeMarco", popularity: 71 },
  { name: "Bon Iver", popularity: 65 },
];

const topTracks = [
  { title: "The Less I Know The Better", artist: "Tame Impala", duration: "3:36" },
  { title: "Do I Wanna Know?", artist: "Arctic Monkeys", duration: "4:32" },
  { title: "Motion Sickness", artist: "Phoebe Bridgers", duration: "4:03" },
  { title: "Chamber of Reflection", artist: "Mac DeMarco", duration: "4:07" },
  { title: "Holocene", artist: "Bon Iver", duration: "5:36" },
];

const hours = [
  2, 1, 0, 0, 0, 1, 3, 8, 12, 15, 18, 22,
  28, 31, 26, 24, 30, 35, 40, 48, 55, 62, 78, 70,
];
const peakIdx = hours.indexOf(Math.max(...hours));

const genres = [
  { name: "Indie Rock", plays: 1240 },
  { name: "Psychedelic", plays: 980 },
  { name: "Alt Rock", plays: 760 },
  { name: "Dream Pop", plays: 540 },
  { name: "Folk", plays: 410 },
];
const maxGenre = Math.max(...genres.map((g) => g.plays));

function Card({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <div className="rounded-2xl border border-[#2A2A2A] bg-[#1A1A1A] p-6">
      <h3 className="text-sm font-semibold uppercase tracking-wider text-[#888888]">{title}</h3>
      <div className="mt-5">{children}</div>
    </div>
  );
}

export default function DashboardPage() {
  const [hasData] = useState(true);

  if (!hasData) {
    return (
      <PageShell>
        <div className="flex min-h-[60vh] flex-col items-center justify-center text-center">
          <Database className="h-10 w-10 text-[#888888]" />
          <p className="mt-4 text-base text-white">
            Tu DWH está vacío. Ve a la pestaña ETL y sincroniza tus datos.
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
        <h1 className="text-2xl font-bold text-white">Your listening, at a glance</h1>
        <p className="mt-1 text-sm text-[#888888]">Last 4 weeks of activity</p>
      </div>

      <div className="grid gap-6 md:grid-cols-2">
        <Card title="Top Artists">
          <ul className="space-y-4">
            {topArtists.map((a, i) => (
              <li key={a.name} className="flex items-center gap-4">
                <span className="w-5 text-sm tabular-nums text-[#888888]">{i + 1}</span>
                <div className="flex-1">
                  <div className="mb-1.5 flex items-center justify-between">
                    <span className="text-sm font-medium text-white">{a.name}</span>
                    <span className="text-xs tabular-nums text-[#888888]">{a.popularity}</span>
                  </div>
                  <div className="h-1.5 w-full overflow-hidden rounded-full bg-[#2A2A2A]">
                    <div className="h-full rounded-full bg-[#1DB954]" style={{ width: `${a.popularity}%` }} />
                  </div>
                </div>
              </li>
            ))}
          </ul>
        </Card>

        <Card title="Top Tracks">
          <ul className="space-y-3">
            {topTracks.map((t, i) => (
              <li key={t.title} className="flex items-center gap-4">
                <span className="w-5 text-sm tabular-nums text-[#888888]">{i + 1}</span>
                <div className="min-w-0 flex-1">
                  <div className="truncate text-sm font-medium text-white">{t.title}</div>
                  <div className="truncate text-xs text-[#888888]">{t.artist}</div>
                </div>
                <span className="text-xs tabular-nums text-[#888888]">{t.duration}</span>
              </li>
            ))}
          </ul>
        </Card>

        <Card title="Peak Listening Hour">
          <div className="text-3xl font-bold tracking-tight text-white">
            {String(peakIdx).padStart(2, "0")}:00 – {String(peakIdx + 1).padStart(2, "0")}:00
          </div>
          <p className="mt-1 text-xs text-[#888888]">Your most active hour of the day</p>
          <div className="mt-6 flex h-24 items-end gap-1">
            {hours.map((v, i) => (
              <div
                key={i}
                className={`flex-1 rounded-sm ${i === peakIdx ? "bg-[#1DB954]" : "bg-[#2A2A2A]"}`}
                style={{ height: `${(v / Math.max(...hours)) * 100}%` }}
                title={`${i}:00`}
              />
            ))}
          </div>
          <div className="mt-2 flex justify-between text-[10px] text-[#888888]">
            <span>00</span><span>06</span><span>12</span><span>18</span><span>23</span>
          </div>
        </Card>

        <Card title="Top Genres">
          <ul className="space-y-4">
            {genres.map((g) => (
              <li key={g.name}>
                <div className="mb-1.5 flex items-center justify-between">
                  <span className="text-sm font-medium text-white">{g.name}</span>
                  <span className="text-xs tabular-nums text-[#888888]">{g.plays.toLocaleString()} plays</span>
                </div>
                <div className="h-2 w-full overflow-hidden rounded-full bg-[#2A2A2A]">
                  <div className="h-full rounded-full bg-[#1DB954]" style={{ width: `${(g.plays / maxGenre) * 100}%` }} />
                </div>
              </li>
            ))}
          </ul>
        </Card>
      </div>
    </PageShell>
  );
}
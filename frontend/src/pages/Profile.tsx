import { ExternalLink } from "lucide-react";
import { PageShell } from "../components/Navbar";

function StatCard({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-2xl border border-[#2A2A2A] bg-[#1A1A1A] p-6">
      <div className="text-xs font-semibold uppercase tracking-wider text-[#888888]">{label}</div>
      <div className="mt-2 text-2xl font-bold text-white">{value}</div>
    </div>
  );
}

export default function ProfilePage() {
  return (
    <PageShell>
      <div className="grid gap-8 md:grid-cols-[320px_1fr]">
        <div className="rounded-2xl border border-[#2A2A2A] bg-[#1A1A1A] p-8 text-center">
          <div className="mx-auto flex h-32 w-32 items-center justify-center rounded-full bg-[#1DB954] text-4xl font-bold text-black">
            AM
          </div>
          <h1 className="mt-6 text-[28px] font-bold leading-tight text-white">Alex Morgan</h1>
          <p className="mt-1 text-sm text-[#888888]">alex.morgan@gmail.com</p>
          <div className="mt-4 flex items-center justify-center gap-2 text-sm text-[#888888]">
            <span>US</span>
          </div>
          <span className="mt-4 inline-block rounded-full bg-[#1DB954] px-3 py-1 text-xs font-semibold text-black">
            Premium
          </span>
        </div>
        <div className="space-y-6">
          <div className="grid gap-6 sm:grid-cols-3">
            <StatCard label="Followers" value="248" />
            <StatCard label="Account type" value="Premium" />
            <StatCard label="Member since" value="Mar 2017" />
          </div>
          <div className="rounded-2xl border border-[#2A2A2A] bg-[#1A1A1A] p-6">
            <h3 className="text-sm font-semibold uppercase tracking-wider text-[#888888]">About</h3>
            <p className="mt-3 text-sm text-white">
              Connected via Spotify Web API. Profile information is synced on each login.
            </p>
          </div>
          
            <a
            href="https://open.spotify.com"
            target="_blank"
            rel="noreferrer"
            className="inline-flex items-center gap-2 rounded-full border border-[#1DB954] px-5 py-2.5 text-sm font-semibold text-[#1DB954] transition-colors hover:bg-[#1DB954] hover:text-black"
          >
            View on Spotify
            <ExternalLink className="h-4 w-4" />
          </a>
        </div>
      </div>
    </PageShell>
  );
}
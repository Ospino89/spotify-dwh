import { createFileRoute } from "@tanstack/react-router";
import { ExternalLink } from "lucide-react";

export const Route = createFileRoute("/_authenticated/profile")({
  head: () => ({ meta: [{ title: "Profile — My Spotify Wrapped" }] }),
  component: ProfilePage,
});

function StatCard({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-2xl border border-border bg-card p-6">
      <div className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">{label}</div>
      <div className="mt-2 text-2xl font-bold text-foreground">{value}</div>
    </div>
  );
}

function ProfilePage() {
  return (
    <div className="grid gap-8 md:grid-cols-[320px_1fr]">
      <div className="rounded-2xl border border-border bg-card p-8 text-center">
        <div className="mx-auto flex h-32 w-32 items-center justify-center rounded-full bg-primary text-4xl font-bold text-primary-foreground">
          AM
        </div>
        <h1 className="mt-6 text-[28px] font-bold leading-tight text-foreground">Alex Morgan</h1>
        <p className="mt-1 text-sm text-muted-foreground">alex.morgan@gmail.com</p>
        <div className="mt-4 flex items-center justify-center gap-2 text-sm text-muted-foreground">
          <span>US</span>
        </div>
        <span className="mt-4 inline-block rounded-full bg-primary px-3 py-1 text-xs font-semibold text-primary-foreground">
          Premium
        </span>
      </div>

      <div className="space-y-6">
        <div className="grid gap-6 sm:grid-cols-3">
          <StatCard label="Followers" value="248" />
          <StatCard label="Account type" value="Premium" />
          <StatCard label="Member since" value="Mar 2017" />
        </div>

        <div className="rounded-2xl border border-border bg-card p-6">
          <h3 className="text-sm font-semibold uppercase tracking-wider text-muted-foreground">About</h3>
          <p className="mt-3 text-sm text-foreground/90">
            Connected via Spotify Web API. Profile information is synced on each login and reflects
            your current public Spotify account details.
          </p>
        </div>

        <a
          href="https://open.spotify.com"
          target="_blank"
          rel="noreferrer"
          className="inline-flex items-center gap-2 rounded-full border border-primary px-5 py-2.5 text-sm font-semibold text-primary transition-colors hover:bg-primary hover:text-primary-foreground"
        >
          View on Spotify
          <ExternalLink className="h-4 w-4" />
        </a>
      </div>
    </div>
  );
}

import { createFileRoute, Link } from "@tanstack/react-router";
import { AppLogo } from "@/components/AppLogo";

export const Route = createFileRoute("/login")({
  head: () => ({
    meta: [
      { title: "Sign in — My Spotify Wrapped" },
      { name: "description", content: "Connect your Spotify account to view your listening analytics." },
    ],
  }),
  component: LoginPage,
});

function SpotifyIcon({ className = "" }: { className?: string }) {
  return (
    <svg viewBox="0 0 24 24" className={className} fill="currentColor" aria-hidden="true">
      <path d="M12 0C5.4 0 0 5.4 0 12s5.4 12 12 12 12-5.4 12-12S18.66 0 12 0zm5.52 17.34a.75.75 0 0 1-1.03.25c-2.82-1.72-6.36-2.11-10.54-1.16a.75.75 0 1 1-.33-1.46c4.56-1.04 8.49-.59 11.65 1.34.36.22.47.69.25 1.03zm1.47-3.27a.94.94 0 0 1-1.29.31c-3.23-1.99-8.16-2.56-11.98-1.4a.94.94 0 1 1-.55-1.8c4.38-1.33 9.81-.69 13.52 1.59.44.27.58.85.3 1.3zm.13-3.41C15.3 8.42 8.4 8.18 4.74 9.29a1.13 1.13 0 1 1-.66-2.16c4.21-1.28 11.83-1.03 16.5 1.74a1.13 1.13 0 1 1-1.16 1.94z" />
    </svg>
  );
}

function LoginPage() {
  return (
    <div className="flex min-h-screen items-center justify-center bg-background px-6">
      <div className="w-full max-w-md rounded-2xl border border-border bg-card p-10 shadow-2xl">
        <div className="flex justify-center">
          <AppLogo size="xl" />
        </div>
        <h1 className="mt-8 text-center text-xl font-semibold text-foreground">
          Welcome back
        </h1>
        <p className="mt-2 text-center text-sm text-muted-foreground">
          Sign in to view your personal listening analytics.
        </p>
        <Link
          to="/callback"
          className="mt-8 flex w-full items-center justify-center gap-3 rounded-full bg-primary px-6 py-3 text-sm font-semibold text-primary-foreground transition-transform hover:scale-[1.02] hover:bg-primary/90"
        >
          <SpotifyIcon className="h-5 w-5" />
          Connect with Spotify
        </Link>
        <p className="mt-6 text-center text-xs text-muted-foreground">
          Your listening data, beautifully analyzed.
        </p>
      </div>
    </div>
  );
}
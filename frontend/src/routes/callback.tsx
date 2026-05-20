import { createFileRoute } from "@tanstack/react-router";

export const Route = createFileRoute("/callback")({
  head: () => ({
    meta: [{ title: "Connecting — My Spotify Wrapped" }],
  }),
  component: CallbackPage,
});

function CallbackPage() {
  return (
    <div className="flex min-h-screen flex-col items-center justify-center gap-6 bg-background px-6">
      <div className="h-12 w-12 animate-spin rounded-full border-2 border-border border-t-primary" />
      <div className="text-center">
        <p className="text-base font-medium text-foreground">Connecting your Spotify account...</p>
        <p className="mt-2 text-sm text-muted-foreground">You'll be redirected automatically.</p>
      </div>
    </div>
  );
}
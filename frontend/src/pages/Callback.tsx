import { useEffect } from "react";
import { useNavigate } from "react-router-dom";

export default function CallbackPage() {
  const navigate = useNavigate();

  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    const token = params.get("token");
    if (token) {
      localStorage.setItem("app_token", token);
      window.history.replaceState({}, "", "/callback");
      navigate("/dashboard");
    } else {
      navigate("/login");
    }
  }, []);

  return (
    <div className="flex min-h-screen flex-col items-center justify-center gap-6 bg-[#0D0D0D] px-6">
      <div className="h-12 w-12 animate-spin rounded-full border-2 border-[#2A2A2A] border-t-[#1DB954]" />
      <div className="text-center">
        <p className="text-base font-medium text-white">Connecting your Spotify account...</p>
        <p className="mt-2 text-sm text-[#888888]">You'll be redirected automatically.</p>
      </div>
    </div>
  );
}
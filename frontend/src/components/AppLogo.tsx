type Size = "sm" | "md" | "lg" | "xl";

const iconSize: Record<Size, number> = { sm: 20, md: 24, lg: 32, xl: 44 };
const textSize: Record<Size, string> = {
  sm: "text-sm",
  md: "text-base",
  lg: "text-xl",
  xl: "text-3xl",
};

export function AppLogoMark({ size = 24, className = "" }: { size?: number; className?: string }) {
  // 5 EQ bars (white) with a green analytics trend-line through their tops + insight dot.
  // Unique mark: music (equalizer) literally being read as a data chart (line + point).
  return (
    <svg
      viewBox="0 0 32 32"
      width={size}
      height={size}
      className={className}
      fill="none"
      aria-hidden="true"
    >
      {/* EQ bars */}
      <rect x="1"  y="18" width="4" height="11" rx="1" fill="#FFFFFF" />
      <rect x="7"  y="11" width="4" height="18" rx="1" fill="#FFFFFF" />
      <rect x="13" y="20" width="4" height="9"  rx="1" fill="#FFFFFF" />
      <rect x="19" y="7"  width="4" height="22" rx="1" fill="#FFFFFF" />
      <rect x="25" y="14" width="4" height="15" rx="1" fill="#FFFFFF" />
      {/* Analytics trend-line connecting bar tops, ending in an upward insight */}
      <polyline
        points="3,18 9,11 15,20 21,7 27,14 31,3"
        stroke="#1DB954"
        strokeWidth="2"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
      {/* Insight data point */}
      <circle cx="31" cy="3" r="2.2" fill="#1DB954" />
    </svg>
  );
}

export function AppLogo({
  size = "md",
  showWordmark = true,
  className = "",
}: {
  size?: Size;
  showWordmark?: boolean;
  className?: string;
}) {
  return (
    <div className={`inline-flex items-center gap-2.5 ${className}`}>
      <AppLogoMark size={iconSize[size]} />
      {showWordmark && (
        <span className={`${textSize[size]} leading-none tracking-tight whitespace-nowrap`}>
          <span className="font-normal text-white">My </span>
          <span className="font-medium text-white">Spotify </span>
          <span className="font-bold text-[#1DB954]">Wrapped</span>
        </span>
      )}
    </div>
  );
}

export default AppLogo;
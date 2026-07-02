/**
 * Mascot.tsx — Python Confidence Coach mascot character.
 * Uses the original hand-drawn mascot image directly.
 */

interface MascotProps {
  size?: number;
  className?: string;
}

/** Full mascot — hero sections, empty states, login page */
export function Mascot({ size = 120, className = "" }: MascotProps) {
  return (
    <img
      src="/mascot.png"
      alt="Python Confidence Coach mascot"
      width={size}
      height={size}
      className={className}
      style={{ objectFit: "contain" }}
    />
  );
}

/** Small avatar — used in AI chat message bubbles */
export function MascotAvatar({ size = 28 }: { size?: number }) {
  return (
    <img
      src="/mascot.png"
      alt="Coach"
      width={size}
      height={size}
      style={{ objectFit: "contain", borderRadius: "50%", background: "#F4F4F4" }}
    />
  );
}

import { MascotAvatar } from "@/components/Mascot";

export function TypingIndicator() {
  return (
    <div className="flex items-center gap-3 py-1 animate-fade-in">
      <div className="flex-shrink-0">
        <MascotAvatar size={28} />
      </div>
      <div
        className="flex items-center gap-1.5 rounded-3xl rounded-tl-md px-4 py-3"
        style={{
          background: "#FFFFFF",
          border: "1px solid #EAEAEA",
          boxShadow: "0 2px 8px rgba(0,0,0,0.06)",
        }}
      >
        {[0, 150, 300].map((delay) => (
          <span
            key={delay}
            className="h-1.5 w-1.5 animate-pulse-soft rounded-full"
            style={{ background: "#BBBBBB", animationDelay: `${delay}ms` }}
          />
        ))}
      </div>
    </div>
  );
}

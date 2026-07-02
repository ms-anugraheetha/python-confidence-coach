interface Props {
  topic: string | null;
}

export function NextChallengeWidget({ topic }: Props) {
  if (!topic) return null;

  return (
    <div
      className="rounded-2xl px-5 py-4"
      style={{
        background: "#111111",
        border: "1px solid #111111",
      }}
    >
      <p className="mb-1.5 text-[11px] font-semibold uppercase tracking-[0.08em] text-[#666666]">
        Up Next
      </p>
      <p
        className="text-[13px] font-semibold text-white"
        style={{ letterSpacing: "-0.01em" }}
      >
        {topic}
      </p>
      <p className="mt-1.5 text-[11px] text-[#555555]">
        Continue your learning journey
      </p>
      <div className="mt-3 flex items-center gap-1.5 text-[11px] font-medium text-[#888888]">
        <svg width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
          <path d="M2 3h6a4 4 0 014 4v14a3 3 0 00-3-3H2z"/><path d="M22 3h-6a4 4 0 00-4 4v14a3 3 0 013-3h7z"/>
        </svg>
        Ask me to teach you this
        <svg width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
          <polyline points="9 18 15 12 9 6"/>
        </svg>
      </div>
    </div>
  );
}

import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { useAuth } from "@/context/AuthContext";
import { HttpError } from "@/api/client";
import { Mascot } from "@/components/Mascot";

function EyeIcon({ open }: { open: boolean }) {
  return open ? (
    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/><circle cx="12" cy="12" r="3"/>
    </svg>
  ) : (
    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M17.94 17.94A10.07 10.07 0 0112 20c-7 0-11-8-11-8a18.45 18.45 0 015.06-5.94"/>
      <path d="M9.9 4.24A9.12 9.12 0 0112 4c7 0 11 8 11 8a18.5 18.5 0 01-2.16 3.19"/>
      <line x1="1" y1="1" x2="23" y2="23"/>
    </svg>
  );
}

function InputField({
  id, label, type, autoComplete, required, value, onChange, placeholder,
  extra, hint, minLength,
}: {
  id: string; label: string; type: string; autoComplete: string;
  required?: boolean; value: string; onChange: (v: string) => void;
  placeholder: string; extra?: React.ReactNode; hint?: string; minLength?: number;
}) {
  const [focused, setFocused] = useState(false);
  return (
    <div className="flex flex-col gap-2">
      <label htmlFor={id} className="text-[12px] font-semibold text-[#666666]">
        {label}
        {!required && <span className="ml-1.5 font-normal text-[#BBBBBB]">(optional)</span>}
      </label>
      <div className="relative">
        <input
          id={id}
          type={type}
          autoComplete={autoComplete}
          required={required}
          minLength={minLength}
          value={value}
          onChange={(e) => onChange(e.target.value)}
          placeholder={placeholder}
          onFocus={() => setFocused(true)}
          onBlur={() => setFocused(false)}
          className="w-full rounded-2xl px-4 py-3 text-[13px] font-medium text-[#111111] placeholder-[#BBBBBB] outline-none transition-all duration-150"
          style={{
            background: "#FFFFFF",
            border: `1px solid ${focused ? "#D4D4D4" : "#EAEAEA"}`,
            boxShadow: focused ? "0 0 0 3px rgba(0,0,0,0.05)" : "none",
          }}
        />
        {extra}
      </div>
      {hint && <p className="text-[11px] text-[#BBBBBB]">{hint}</p>}
    </div>
  );
}

export function RegisterPage() {
  const { register } = useAuth();
  const navigate = useNavigate();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [displayName, setDisplayName] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [showPassword, setShowPassword] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setIsLoading(true);
    try {
      await register({ email, password, display_name: displayName || undefined });
      navigate("/coach");
    } catch (err) {
      if (err instanceof HttpError) {
        setError(err.error.message);
      } else {
        setError("Something went wrong. Please try again.");
      }
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="flex min-h-screen" style={{ background: "#FAFAFA" }}>

      {/* Left panel */}
      <div
        className="hidden lg:flex lg:w-1/2 flex-col justify-between p-14"
        style={{ background: "#FFFFFF", borderRight: "1px solid #EAEAEA" }}
      >
        <div className="flex items-center gap-3">
          <div className="flex h-9 w-9 items-center justify-center rounded-xl" style={{ background: "#111111" }}>
            <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
              <circle cx="5" cy="8" r="3" fill="white" fillOpacity="0.9"/>
              <circle cx="11" cy="8" r="3" fill="white" fillOpacity="0.5"/>
            </svg>
          </div>
          <span className="text-[14px] font-bold text-[#111111]">Python Confidence Coach</span>
        </div>

        <div className="flex items-end gap-8">
          <div>
            <p
              className="font-bold leading-none select-none"
              style={{ fontSize: "clamp(5rem, 10vw, 9rem)", letterSpacing: "-0.04em", lineHeight: 0.88, color: "#EEEEEE" }}
            >
              01.
            </p>
            <p className="mt-8 max-w-xs text-[13px] leading-relaxed text-[#999999]">
              Your progress is tracked across every conversation. The more you engage, the more precisely we can guide you.
            </p>
          </div>
          <Mascot size={120} className="flex-shrink-0 mb-2" />
        </div>

        <p className="text-[11px] text-[#CCCCCC]">Python Confidence Coach</p>
      </div>

      {/* Right form panel */}
      <div className="flex flex-1 flex-col items-center justify-center px-8 py-16">
        <div className="w-full max-w-[380px] animate-fade-in">

          {/* Mobile wordmark */}
          <div className="mb-10 flex items-center gap-3 lg:hidden">
            <div className="flex h-8 w-8 items-center justify-center rounded-xl" style={{ background: "#111111" }}>
              <svg width="14" height="14" viewBox="0 0 16 16" fill="none">
                <circle cx="5" cy="8" r="3" fill="white" fillOpacity="0.9"/>
                <circle cx="11" cy="8" r="3" fill="white" fillOpacity="0.5"/>
              </svg>
            </div>
            <span className="text-[14px] font-bold text-[#111111]">Python Confidence Coach</span>
          </div>

          <div className="mb-8">
            <h1 className="text-[26px] font-bold text-[#111111]" style={{ letterSpacing: "-0.025em" }}>
              Create your account
            </h1>
            <p className="mt-1.5 text-[13px] text-[#999999]">
              Free forever. Your progress, saved.
            </p>
          </div>

          <form onSubmit={handleSubmit} className="flex flex-col gap-4">
            {error && (
              <div
                className="rounded-2xl px-4 py-3 text-[13px] text-[#666666]"
                style={{ background: "#FFF8F8", border: "1px solid #EAEAEA" }}
              >
                {error}
              </div>
            )}

            <InputField
              id="name" label="Name" type="text" autoComplete="name"
              value={displayName} onChange={setDisplayName} placeholder="Python Learner"
            />

            <InputField
              id="email" label="Email" type="email" autoComplete="email"
              required value={email} onChange={setEmail} placeholder="you@example.com"
            />

            <InputField
              id="password" label="Password" type={showPassword ? "text" : "password"}
              autoComplete="new-password" required minLength={6}
              value={password} onChange={setPassword} placeholder="Min 6 characters"
              hint="At least 6 characters"
              extra={
                <button
                  type="button"
                  onClick={() => setShowPassword((v) => !v)}
                  className="absolute right-3.5 top-1/2 -translate-y-1/2 text-[#BBBBBB] transition-colors hover:text-[#666666]"
                  aria-label={showPassword ? "Hide password" : "Show password"}
                >
                  <EyeIcon open={showPassword} />
                </button>
              }
            />

            <button
              type="submit"
              disabled={isLoading}
              className="mt-2 w-full rounded-2xl py-3.5 text-[13px] font-semibold text-white transition-all hover:opacity-90 disabled:opacity-40"
              style={{ background: "#111111" }}
            >
              {isLoading ? "Creating account…" : "Create account"}
            </button>
          </form>

          <p className="mt-6 text-[13px] text-[#999999]">
            Already have an account?{" "}
            <Link
              to="/login"
              className="font-semibold text-[#111111] underline underline-offset-4 decoration-[#CCCCCC] hover:decoration-[#111111] transition-all"
            >
              Sign in
            </Link>
          </p>
        </div>
      </div>
    </div>
  );
}

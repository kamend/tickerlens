"use client";

import { useRouter } from "next/navigation";
import { FormEvent, useState } from "react";
import { validateTicker } from "@/lib/api";

export default function TickerInput() {
  const router = useRouter();
  const [ticker, setTicker] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  async function onSubmit(e: FormEvent) {
    e.preventDefault();
    const trimmed = ticker.trim().toUpperCase();
    if (!trimmed || loading) return;
    setLoading(true);
    setError(null);
    try {
      const result = await validateTicker(trimmed);
      if (result.valid) {
        router.push(`/results/${trimmed}`);
        return;
      }
      setError(result.error);
      setLoading(false);
    } catch {
      setError("Couldn't reach the server. Is the backend running?");
      setLoading(false);
    }
  }

  return (
    <form onSubmit={onSubmit} className="w-full max-w-md">
      <div className="relative">
        <input
          type="text"
          inputMode="text"
          autoComplete="off"
          autoCorrect="off"
          spellCheck={false}
          autoFocus
          value={ticker}
          onChange={(e) => {
            setTicker(e.target.value);
            if (error) setError(null);
          }}
          placeholder="Enter a ticker — AAPL, FIG, TSLA…"
          disabled={loading}
          aria-label="Ticker symbol"
          aria-invalid={error ? true : undefined}
          className="w-full bg-transparent border-b border-foreground/20 pl-1 pr-14 py-3 text-lg md:text-xl font-serif tracking-wide text-foreground placeholder:text-muted/60 placeholder:normal-case placeholder:tracking-normal focus:border-accent focus:outline-none transition-colors duration-300 disabled:opacity-60 uppercase"
        />
        <button
          type="submit"
          disabled={loading || !ticker.trim()}
          aria-label="Research ticker"
          className="absolute right-0 top-1/2 -translate-y-1/2 h-10 w-10 flex items-center justify-center rounded-full bg-accent text-background hover:bg-accent-hover disabled:opacity-30 disabled:cursor-not-allowed transition-all duration-200 font-sans"
        >
          {loading ? (
            <span
              aria-hidden
              className="h-4 w-4 rounded-full border-2 border-background/40 border-t-background animate-spin"
            />
          ) : (
            <svg
              aria-hidden
              width="16"
              height="16"
              viewBox="0 0 16 16"
              fill="none"
              stroke="currentColor"
              strokeWidth="1.75"
              strokeLinecap="round"
              strokeLinejoin="round"
            >
              <path d="M3 8h10" />
              <path d="M9 4l4 4-4 4" />
            </svg>
          )}
        </button>
      </div>
      <div
        aria-live="polite"
        className={`mt-4 font-sans text-sm text-danger transition-opacity duration-300 ${
          error ? "opacity-100" : "opacity-0"
        }`}
      >
        {error ?? " "}
      </div>
    </form>
  );
}

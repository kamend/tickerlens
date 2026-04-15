"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import type { Briefing, ErrorEvent, HeaderData } from "@/lib/types";
import { streamResearch } from "@/lib/sse";
import CompanyHeader from "./CompanyHeader";
import ProgressDisplay from "./ProgressDisplay";

interface ResultsViewProps {
  ticker: string;
}

export default function ResultsView({ ticker }: ResultsViewProps) {
  const [header, setHeader] = useState<HeaderData | null>(null);
  const [progress, setProgress] = useState<string | null>(null);
  const [briefing, setBriefing] = useState<Briefing | null>(null);
  const [error, setError] = useState<ErrorEvent | null>(null);

  useEffect(() => {
    const controller = new AbortController();
    setProgress(`Looking up ${ticker}…`);

    streamResearch(
      ticker,
      {
        onProgress: (ev) => setProgress(ev.message),
        onHeader: (ev) => setHeader(ev),
        onResult: (ev) => {
          setBriefing(ev);
          setProgress(null);
        },
        onError: (ev) => {
          setError(ev);
          setProgress(null);
        },
      },
      controller.signal,
    ).catch(() => {
      // stream closed / aborted — swallow; state drives UI
    });

    return () => controller.abort();
  }, [ticker]);

  const showLoadingHeader = !header && !error;
  const showProgress = !briefing && !error;

  return (
    <main className="flex flex-1 flex-col items-center px-6 py-16 md:py-24">
      <div className="w-full max-w-3xl flex flex-col gap-12">
        {showLoadingHeader ? (
          <section className="flex flex-col gap-3 animate-fade-in-up">
            <p className="font-sans text-xs uppercase tracking-[0.22em] text-muted">
              {ticker}
            </p>
            <h1 className="font-serif text-3xl md:text-4xl text-muted italic">
              Loading…
            </h1>
          </section>
        ) : header ? (
          <CompanyHeader data={header} />
        ) : null}

        {showProgress && <ProgressDisplay message={progress} />}

        {briefing && (
          <section className="animate-fade-in-up">
            <p className="font-serif text-muted italic">
              Perspective cards land in step 9b.
            </p>
          </section>
        )}

        {error && (
          <section className="flex flex-col gap-4 animate-fade-in-up">
            <p className="font-serif text-lg text-foreground">{error.message}</p>
            <Link
              href="/"
              className="font-sans text-sm text-accent hover:text-accent-hover transition-colors"
            >
              ← Back
            </Link>
          </section>
        )}
      </div>
    </main>
  );
}

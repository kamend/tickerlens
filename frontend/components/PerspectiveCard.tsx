"use client";

import { useId, useState } from "react";
import type { Argument, Confidence } from "@/lib/types";

interface PerspectiveCardProps {
  stance: "buy" | "hold" | "sell";
  argument: Argument;
}

const titles: Record<PerspectiveCardProps["stance"], string> = {
  buy: "The case for buying",
  hold: "The case for holding",
  sell: "The case for selling",
};

const confidenceLabel: Record<Confidence, string> = {
  strong: "Evidence: strong",
  moderate: "Evidence: moderate",
  thin: "Evidence: thin",
};

export default function PerspectiveCard({ stance, argument }: PerspectiveCardProps) {
  const [open, setOpen] = useState(false);
  const regionId = useId();

  const paragraphs = argument.reasoning
    .split(/\n{2,}/)
    .map((p) => p.trim())
    .filter(Boolean);

  return (
    <article className="border-t border-subtle pt-8 first:border-t-0 first:pt-0">
      <button
        type="button"
        onClick={() => setOpen((v) => !v)}
        aria-expanded={open}
        aria-controls={regionId}
        className="group w-full text-left flex flex-col gap-3 cursor-pointer"
      >
        <div className="flex items-baseline justify-between gap-4">
          <h2 className="font-serif text-2xl md:text-[1.75rem] text-foreground">
            {titles[stance]}
          </h2>
          <span
            aria-hidden
            className={`font-sans text-xl text-muted transition-transform duration-300 ${
              open ? "rotate-45" : ""
            }`}
          >
            +
          </span>
        </div>
        <p className="font-serif text-lg leading-relaxed text-foreground/90">
          {argument.summary}
        </p>
        <span className="font-sans text-[11px] uppercase tracking-[0.18em] text-muted">
          {confidenceLabel[argument.confidence]}
        </span>
      </button>

      <div
        id={regionId}
        className={`grid transition-[grid-template-rows] duration-500 ease-out ${
          open ? "grid-rows-[1fr] mt-6" : "grid-rows-[0fr] mt-0"
        }`}
      >
        <div className="overflow-hidden">
          <div
            className={`flex flex-col gap-5 transition-opacity duration-300 ${
              open ? "opacity-100 delay-150" : "opacity-0"
            }`}
          >
            {paragraphs.map((para, i) => (
              <p
                key={i}
                className="font-serif text-base md:text-[1.0625rem] leading-[1.75] text-foreground/85"
              >
                {para}
              </p>
            ))}

            {argument.citations.length > 0 && (
              <div className="flex flex-col gap-3 border-t border-subtle pt-5 mt-2">
                <span className="font-sans text-[11px] uppercase tracking-[0.22em] text-muted">
                  Sources
                </span>
                <ul className="flex flex-col gap-2">
                  {argument.citations.map((c, i) => (
                    <li key={i}>
                      <a
                        href={c.url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="font-serif text-sm text-accent hover:text-accent-hover underline-offset-4 hover:underline transition-colors"
                      >
                        {c.title}
                      </a>
                    </li>
                  ))}
                </ul>
              </div>
            )}
          </div>
        </div>
      </div>
    </article>
  );
}

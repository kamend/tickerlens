"use client";

import { useRouter } from "next/navigation";
import { useState, useTransition } from "react";

interface ErrorStateProps {
  message: string;
}

export default function ErrorState({ message }: ErrorStateProps) {
  const router = useRouter();
  const [leaving, setLeaving] = useState(false);
  const [, startTransition] = useTransition();

  const handleBack = () => {
    setLeaving(true);
    setTimeout(() => {
      startTransition(() => router.push("/"));
    }, 300);
  };

  return (
    <section
      className={`flex flex-col gap-6 transition-opacity duration-300 ${
        leaving ? "opacity-0" : "opacity-100 animate-fade-in-up"
      }`}
    >
      <p className="font-serif text-xl md:text-2xl leading-relaxed text-foreground">
        {message}
      </p>
      <p className="font-serif text-base text-muted italic">
        Something interrupted the research. Head back and try again.
      </p>
      <button
        type="button"
        onClick={handleBack}
        className="self-start font-sans text-sm text-accent hover:text-accent-hover transition-colors cursor-pointer"
      >
        ← Back to search
      </button>
    </section>
  );
}

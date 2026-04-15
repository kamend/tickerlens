"use client";

import { useEffect, useState } from "react";

interface ProgressDisplayProps {
  message: string | null;
}

export default function ProgressDisplay({ message }: ProgressDisplayProps) {
  const [visible, setVisible] = useState<string | null>(message);
  const [phase, setPhase] = useState<"in" | "out">("in");

  useEffect(() => {
    if (message === visible) return;
    setPhase("out");
    const t = setTimeout(() => {
      setVisible(message);
      setPhase("in");
    }, 280);
    return () => clearTimeout(t);
  }, [message, visible]);

  return (
    <div className="min-h-[2.5rem] flex items-center justify-center" aria-live="polite">
      <p
        className={`font-serif text-lg md:text-xl text-muted italic transition-opacity duration-300 ease-out ${
          phase === "in" ? "opacity-100" : "opacity-0"
        }`}
      >
        {visible ?? "\u00a0"}
      </p>
    </div>
  );
}

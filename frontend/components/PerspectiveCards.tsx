import type { Briefing } from "@/lib/types";
import PerspectiveCard from "./PerspectiveCard";

interface PerspectiveCardsProps {
  briefing: Briefing;
}

export default function PerspectiveCards({ briefing }: PerspectiveCardsProps) {
  return (
    <section className="flex flex-col gap-8 animate-fade-in-up">
      <PerspectiveCard stance="buy" argument={briefing.buy} />
      <PerspectiveCard stance="hold" argument={briefing.hold} />
      <PerspectiveCard stance="sell" argument={briefing.sell} />
    </section>
  );
}

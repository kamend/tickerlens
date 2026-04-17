import TickerInput from "@/components/TickerInput";

export default function Home() {
  return (
    <main className="flex flex-1 flex-col items-center justify-center px-6 py-16 animate-fade-in-up">
      <div className="w-full max-w-2xl flex flex-col items-center text-center gap-10">
        <header className="flex flex-col gap-3">
          <p className="font-sans text-sm uppercase tracking-[0.3em] text-foreground">
            TickerLens
          </p>
          <h1 className="text-2xl md:text-3xl font-serif leading-snug text-foreground">
            Three perspectives on any ticker.
          </h1>
          <p className="font-serif text-base text-muted max-w-md mx-auto leading-relaxed">
            Enter a symbol. We&rsquo;ll read the fundamentals, scan the news,
            and write the case for buying, holding, and selling.
          </p>
        </header>
        <TickerInput />
      </div>
    </main>
  );
}

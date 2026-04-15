import Link from "next/link";

export default async function ResultsPage({
  params,
}: {
  params: Promise<{ ticker: string }>;
}) {
  const { ticker } = await params;
  return (
    <main className="flex flex-1 flex-col items-center justify-center px-6 py-16">
      <div className="w-full max-w-2xl flex flex-col items-center text-center gap-6">
        <p className="font-sans text-xs uppercase tracking-[0.25em] text-muted">
          {ticker.toUpperCase()}
        </p>
        <h1 className="text-3xl md:text-4xl font-serif text-foreground">
          Research coming soon.
        </h1>
        <p className="font-serif text-muted">
          The progress stream and perspective cards land in steps 9a &amp; 9b.
        </p>
        <Link
          href="/"
          className="font-sans text-sm text-accent hover:text-accent-hover transition-colors"
        >
          ← Back
        </Link>
      </div>
    </main>
  );
}

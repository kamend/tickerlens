import ResultsView from "@/components/ResultsView";

export default async function ResultsPage({
  params,
}: {
  params: Promise<{ ticker: string }>;
}) {
  const { ticker } = await params;
  return <ResultsView ticker={ticker.toUpperCase()} />;
}

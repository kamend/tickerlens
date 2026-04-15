export type Confidence = "strong" | "moderate" | "thin";

export interface Citation {
  title: string;
  url: string;
}

export interface Argument {
  summary: string;
  reasoning: string;
  confidence: Confidence;
  citations: Citation[];
}

export interface Briefing {
  buy: Argument;
  hold: Argument;
  sell: Argument;
}

export interface HeaderMetrics {
  market_cap: number | null;
  pe_trailing: number | null;
  fifty_two_week_low: number | null;
  fifty_two_week_high: number | null;
  dividend_yield: number | null;
  change_pct: number | null;
}

export interface HeaderData {
  company_name: string;
  ticker: string;
  sector: string | null;
  price: number | null;
  metrics: HeaderMetrics;
}

export interface ProgressEvent {
  node: string;
  message: string;
}

export interface ErrorEvent {
  message: string;
}

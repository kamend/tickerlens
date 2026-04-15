import type { HeaderData } from "@/lib/types";

interface CompanyHeaderProps {
  data: HeaderData;
}

const compactCurrency = new Intl.NumberFormat("en-US", {
  notation: "compact",
  maximumFractionDigits: 2,
  style: "currency",
  currency: "USD",
});

const price2 = new Intl.NumberFormat("en-US", {
  minimumFractionDigits: 2,
  maximumFractionDigits: 2,
});

function formatPrice(value: number | null): string {
  return value == null ? "—" : `$${price2.format(value)}`;
}

function formatPct(value: number | null): string {
  if (value == null) return "—";
  const sign = value > 0 ? "+" : "";
  return `${sign}${value.toFixed(2)}%`;
}

function formatMarketCap(value: number | null): string {
  return value == null ? "—" : compactCurrency.format(value);
}

function formatPE(value: number | null): string {
  return value == null ? "—" : value.toFixed(1);
}

function formatDividendYield(value: number | null): string {
  if (value == null) return "—";
  return `${value.toFixed(2)}%`;
}

function FiftyTwoWeekRange({
  low,
  high,
  price,
}: {
  low: number | null;
  high: number | null;
  price: number | null;
}) {
  if (low == null || high == null || high <= low) {
    return <span className="text-muted">—</span>;
  }
  const markerPct =
    price == null ? null : Math.min(100, Math.max(0, ((price - low) / (high - low)) * 100));

  return (
    <div className="flex flex-col gap-1.5 w-full max-w-[200px]">
      <div className="relative h-[2px] bg-subtle rounded-full">
        {markerPct != null && (
          <div
            className="absolute top-1/2 -translate-y-1/2 -translate-x-1/2 h-2.5 w-2.5 rounded-full bg-accent"
            style={{ left: `${markerPct}%` }}
            aria-hidden
          />
        )}
      </div>
      <div className="flex justify-between font-sans text-[11px] tabular-nums text-muted">
        <span>${price2.format(low)}</span>
        <span>${price2.format(high)}</span>
      </div>
    </div>
  );
}

function Metric({
  label,
  children,
}: {
  label: string;
  children: React.ReactNode;
}) {
  return (
    <div className="flex flex-col gap-1.5">
      <span className="font-sans text-[11px] uppercase tracking-[0.18em] text-muted">
        {label}
      </span>
      <span className="font-sans text-base tabular-nums text-foreground">{children}</span>
    </div>
  );
}

export default function CompanyHeader({ data }: CompanyHeaderProps) {
  const { company_name, ticker, sector, price, metrics } = data;
  const changePct = metrics.change_pct;
  const changeColor =
    changePct == null
      ? "text-muted"
      : changePct >= 0
        ? "text-accent"
        : "text-danger";

  return (
    <section className="w-full max-w-3xl flex flex-col gap-8 animate-fade-in-up">
      <div className="flex flex-col gap-3">
        <div className="flex items-baseline gap-3 flex-wrap">
          <h1 className="font-serif text-3xl md:text-4xl text-foreground">
            {company_name}
          </h1>
          <span className="font-sans text-sm tracking-[0.2em] text-muted">
            {ticker}
          </span>
        </div>
        {sector && (
          <span className="font-sans text-xs uppercase tracking-[0.22em] text-muted">
            {sector}
          </span>
        )}
        <div className="flex items-baseline gap-3 mt-2">
          <span className="font-serif text-3xl md:text-4xl tabular-nums text-foreground">
            {formatPrice(price)}
          </span>
          <span className={`font-sans text-base tabular-nums ${changeColor}`}>
            {formatPct(changePct)}
          </span>
        </div>
      </div>

      <div className="grid grid-cols-2 md:grid-cols-4 gap-x-8 gap-y-6 border-t border-subtle pt-6">
        <Metric label="Market cap">{formatMarketCap(metrics.market_cap)}</Metric>
        <Metric label="P/E (trailing)">{formatPE(metrics.pe_trailing)}</Metric>
        <Metric label="52-week range">
          <FiftyTwoWeekRange
            low={metrics.fifty_two_week_low}
            high={metrics.fifty_two_week_high}
            price={price}
          />
        </Metric>
        <Metric label="Dividend yield">
          {formatDividendYield(metrics.dividend_yield)}
        </Metric>
      </div>
    </section>
  );
}

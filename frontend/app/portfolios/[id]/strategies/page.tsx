"use client";

import Link from "next/link";
import { useParams } from "next/navigation";
import { useEffect, useState } from "react";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { api, ApiError } from "@/lib/api";

type InstrumentBrief = { id: string; trading_symbol: string; exchange: string };
type Instrument = InstrumentBrief & { name: string };
type Strategy = {
  id: string;
  instrument: InstrumentBrief;
  name: string;
  segment: string;
  quantity: number;
  is_active: boolean;
  entry_score_threshold: string;
  exit_score_threshold: string;
  paused_until: string | null;
  last_evaluated_at: string | null;
};

const WEIGHT_FIELDS = [
  { key: "rsi_weight", label: "RSI (oversold/overbought)" },
  { key: "sma_crossover_weight", label: "SMA crossover (trend)" },
  { key: "macd_weight", label: "MACD" },
  { key: "volume_spike_weight", label: "Volume spike (confirmation)" },
  { key: "momentum_weight", label: "Momentum" },
] as const;

export default function StrategiesPage() {
  const { id: portfolioId } = useParams<{ id: string }>();
  const [strategies, setStrategies] = useState<Strategy[]>([]);
  const [error, setError] = useState<string | null>(null);

  const [query, setQuery] = useState("");
  const [results, setResults] = useState<Instrument[]>([]);
  const [selected, setSelected] = useState<Instrument | null>(null);
  const [name, setName] = useState("");
  const [segment, setSegment] = useState("EQUITY_INTRADAY");
  const [quantity, setQuantity] = useState("1");
  const [weights, setWeights] = useState<Record<string, string>>({
    rsi_weight: "1", sma_crossover_weight: "1", macd_weight: "1", volume_spike_weight: "1", momentum_weight: "1",
  });
  const [entryThreshold, setEntryThreshold] = useState("0.5");
  const [exitThreshold, setExitThreshold] = useState("-0.3");
  const [trailingStop, setTrailingStop] = useState("2");
  const [maxDailyLoss, setMaxDailyLoss] = useState("2000");
  const [creating, setCreating] = useState(false);

  useEffect(() => {
    refresh();
  }, [portfolioId]);

  useEffect(() => {
    if (query.length < 2) {
      setResults([]);
      return;
    }
    const handle = setTimeout(async () => {
      try {
        setResults(await api.get<Instrument[]>(`/instruments/search?q=${encodeURIComponent(query)}`));
      } catch {
        setResults([]);
      }
    }, 250);
    return () => clearTimeout(handle);
  }, [query]);

  async function refresh() {
    try {
      setStrategies(await api.get<Strategy[]>(`/portfolios/${portfolioId}/strategies`));
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Could not load strategies.");
    }
  }

  async function toggleActive(s: Strategy) {
    try {
      await api.post(`/portfolios/${portfolioId}/strategies/${s.id}/${s.is_active ? "deactivate" : "activate"}`);
      await refresh();
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Could not update strategy.");
    }
  }

  async function onCreate(e: React.FormEvent) {
    e.preventDefault();
    if (!selected) return;
    setError(null);
    setCreating(true);
    try {
      await api.post(`/portfolios/${portfolioId}/strategies`, {
        instrument_id: selected.id,
        name,
        segment,
        quantity: Number(quantity),
        entry_score_threshold: entryThreshold,
        exit_score_threshold: exitThreshold,
        trailing_stop_pct: trailingStop,
        max_daily_loss: maxDailyLoss,
        ...Object.fromEntries(Object.entries(weights).map(([k, v]) => [k, v])),
      });
      setName("");
      setSelected(null);
      await refresh();
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Could not create strategy.");
    } finally {
      setCreating(false);
    }
  }

  return (
    <div className="mx-auto max-w-2xl p-8">
      <Link href={`/portfolios/${portfolioId}`} className="text-sm text-accent hover:underline">
        ← Portfolio
      </Link>
      <h1 className="mt-2 text-2xl font-semibold">Strategies</h1>
      <p className="mt-1 text-sm text-ink/60 dark:text-paper/60">
        Auto-trading, built without writing code — set thresholds below and the strategy trades your paper portfolio
        for you. Every trade goes through the same order engine and cost calculations as a manual order.
      </p>

      {strategies.length > 0 && (
        <div className="mt-6 space-y-3">
          {strategies.map((s) => (
            <Card key={s.id} className="flex items-center justify-between">
              <Link href={`/portfolios/${portfolioId}/strategies/${s.id}`} className="flex-1">
                <p className="font-medium">{s.name}</p>
                <p className="text-sm text-ink/50 dark:text-paper/50">
                  {s.instrument.trading_symbol} · {s.segment.replace("_", " ")} · qty {s.quantity}
                </p>
                {s.paused_until && <p className="text-xs text-caution">Paused until {s.paused_until} (daily loss limit)</p>}
              </Link>
              <Button variant="ghost" onClick={() => toggleActive(s)}>
                {s.is_active ? "Deactivate" : "Activate"}
              </Button>
            </Card>
          ))}
        </div>
      )}

      <Card className="mt-6">
        <form onSubmit={onCreate} className="space-y-4">
          <h2 className="font-medium">New strategy</h2>

          <Input label="Strategy name" required value={name} onChange={(e) => setName(e.target.value)} placeholder="e.g. RELIANCE momentum" />

          <div className="relative">
            <Input
              label="Instrument"
              placeholder="Search e.g. RELIANCE"
              value={selected ? `${selected.trading_symbol} — ${selected.name}` : query}
              onChange={(e) => {
                setSelected(null);
                setQuery(e.target.value);
              }}
            />
            {results.length > 0 && !selected && (
              <ul className="absolute z-10 mt-1 w-full rounded-md border border-ink/10 bg-white shadow-lg dark:border-paper/10 dark:bg-ink-soft">
                {results.map((r) => (
                  <li key={r.id} className="cursor-pointer px-3 py-2 text-sm hover:bg-accent/10" onClick={() => { setSelected(r); setResults([]); }}>
                    <span className="font-medium">{r.trading_symbol}</span> <span className="text-ink/50 dark:text-paper/50">{r.name}</span>
                  </li>
                ))}
              </ul>
            )}
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div className="flex flex-col gap-1.5">
              <label className="text-sm font-medium text-ink/80 dark:text-paper/80">Segment</label>
              <select value={segment} onChange={(e) => setSegment(e.target.value)} className="rounded-md border border-ink/15 bg-white px-3 py-2 text-sm dark:border-paper/20 dark:bg-ink-soft">
                <option value="EQUITY_INTRADAY">Equity intraday</option>
                <option value="EQUITY_DELIVERY">Equity delivery</option>
              </select>
              <p className="text-xs text-ink/50 dark:text-paper/50">
                Derivative strategies are disabled until verified contract data and risk controls are implemented.
              </p>
            </div>
            <Input label="Quantity per trade" type="number" min={1} required value={quantity} onChange={(e) => setQuantity(e.target.value)} />
          </div>

          <div>
            <p className="mb-2 text-sm font-medium text-ink/80 dark:text-paper/80">Indicator weights</p>
            <p className="mb-3 text-xs text-ink/50 dark:text-paper/50">
              Each indicator contributes a signal from -1 (bearish) to +1 (bullish); weights combine them into one
              score. Set a weight to 0 to turn an indicator off entirely.
            </p>
            <div className="space-y-3">
              {WEIGHT_FIELDS.map((f) => (
                <div key={f.key} className="flex items-center justify-between gap-4">
                  <label className="text-sm text-ink/70 dark:text-paper/70">{f.label}</label>
                  <input
                    type="number" step="0.1" min={0} max={3} value={weights[f.key]}
                    onChange={(e) => setWeights((w) => ({ ...w, [f.key]: e.target.value }))}
                    className="w-20 rounded-md border border-ink/15 bg-white px-2 py-1 text-sm tabular dark:border-paper/20 dark:bg-ink-soft"
                  />
                </div>
              ))}
            </div>
          </div>

          <div className="grid grid-cols-2 gap-4">
            <Input label="Entry threshold (-1 to 1)" type="number" step="0.1" min={-1} max={1} required value={entryThreshold} onChange={(e) => setEntryThreshold(e.target.value)} />
            <Input label="Exit threshold (-1 to 1)" type="number" step="0.1" min={-1} max={1} required value={exitThreshold} onChange={(e) => setExitThreshold(e.target.value)} />
          </div>
          <div className="grid grid-cols-2 gap-4">
            <Input label="Trailing stop (%)" type="number" step="0.5" min={0.5} required value={trailingStop} onChange={(e) => setTrailingStop(e.target.value)} />
            <Input label="Max daily loss (₹)" type="number" min={1} required value={maxDailyLoss} onChange={(e) => setMaxDailyLoss(e.target.value)} />
          </div>
          <p className="-mt-2 text-xs text-ink/50 dark:text-paper/50">
            If this strategy's realized loss today reaches the daily loss limit, it pauses itself automatically until
            tomorrow.
          </p>

          {error && <p className="text-sm text-loss">{error}</p>}

          <Button type="submit" disabled={!selected || !name || creating} className="w-full">
            {creating ? "Creating…" : "Create strategy (starts inactive)"}
          </Button>
        </form>
      </Card>
    </div>
  );
}

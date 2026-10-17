"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { api, ApiError } from "@/lib/api";

type InstrumentBrief = { id: string; trading_symbol: string; exchange: string };
type Instrument = InstrumentBrief & { name: string };
type Backtest = {
  id: string;
  instrument: InstrumentBrief;
  name: string;
  from_date: string;
  to_date: string;
  status: string;
  error_message: string | null;
  net_pnl: string | null;
  total_trades: number;
  win_count: number;
  loss_count: number;
};

export default function BacktestsPage() {
  const [backtests, setBacktests] = useState<Backtest[]>([]);
  const [error, setError] = useState<string | null>(null);

  const [query, setQuery] = useState("");
  const [results, setResults] = useState<Instrument[]>([]);
  const [selected, setSelected] = useState<Instrument | null>(null);
  const [name, setName] = useState("");
  const [segment, setSegment] = useState("EQUITY_INTRADAY");
  const [fromDate, setFromDate] = useState("");
  const [toDate, setToDate] = useState("");
  const [capital, setCapital] = useState("100000");
  const [quantity, setQuantity] = useState("1");
  const [entryThreshold, setEntryThreshold] = useState("0.5");
  const [exitThreshold, setExitThreshold] = useState("-0.3");
  const [trailingStop, setTrailingStop] = useState("2");
  const [slippage, setSlippage] = useState("5");
  const [running, setRunning] = useState(false);

  useEffect(() => {
    refresh();
    const today = new Date();
    const twoWeeksAgo = new Date(today.getTime() - 14 * 86400000);
    setToDate(today.toISOString().slice(0, 10));
    setFromDate(twoWeeksAgo.toISOString().slice(0, 10));
  }, []);

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
      setBacktests(await api.get<Backtest[]>("/backtests"));
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Could not load backtests.");
    }
  }

  async function onRun(e: React.FormEvent) {
    e.preventDefault();
    if (!selected) return;
    setError(null);
    setRunning(true);
    try {
      await api.post("/backtests", {
        instrument_id: selected.id, name, segment, from_date: fromDate, to_date: toDate,
        initial_capital: capital, quantity: Number(quantity),
        entry_score_threshold: entryThreshold, exit_score_threshold: exitThreshold,
        trailing_stop_pct: trailingStop, slippage_bps: slippage,
      });
      setName("");
      setSelected(null);
      await refresh();
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Could not run backtest.");
    } finally {
      setRunning(false);
    }
  }

  return (
    <div className="mx-auto max-w-2xl p-8">
      <Link href="/" className="text-sm text-accent hover:underline">
        ← Dashboard
      </Link>
      <h1 className="mt-2 text-2xl font-semibold">Backtests</h1>
      <p className="mt-1 text-sm text-ink/60 dark:text-paper/60">
        Runs the exact same scoring and cost engine live strategies use, against historical prices instead of a live
        broker session — a standalone what-if tool, separate from your portfolios.
      </p>

      {backtests.length > 0 && (
        <div className="mt-6 space-y-3">
          {backtests.map((b) => (
            <Link key={b.id} href={`/backtests/${b.id}`}>
              <Card className="flex items-center justify-between hover:border-accent">
                <div>
                  <p className="font-medium">{b.name}</p>
                  <p className="text-sm text-ink/50 dark:text-paper/50">
                    {b.instrument.trading_symbol} · {b.from_date} → {b.to_date}
                  </p>
                </div>
                {b.status === "COMPLETED" ? (
                  <p className={`tabular text-lg ${Number(b.net_pnl) >= 0 ? "text-gain" : "text-loss"}`}>
                    {Number(b.net_pnl) >= 0 ? "+" : ""}₹{Number(b.net_pnl).toLocaleString("en-IN", { maximumFractionDigits: 0 })}
                  </p>
                ) : (
                  <span className={`rounded-full px-2 py-0.5 text-xs font-medium ${b.status === "FAILED" ? "bg-loss/15 text-loss" : "bg-caution/15 text-caution"}`}>
                    {b.status}
                  </span>
                )}
              </Card>
            </Link>
          ))}
        </div>
      )}

      <Card className="mt-6">
        <form onSubmit={onRun} className="space-y-4">
          <h2 className="font-medium">New backtest</h2>
          <p className="text-xs text-ink/50 dark:text-paper/50">Needs a connected broker (Settings → Broker) to fetch historical prices.</p>

          <Input label="Name" required value={name} onChange={(e) => setName(e.target.value)} placeholder="e.g. ICICIBANK momentum, Aug 2026" />

          <div className="relative">
            <Input
              label="Instrument"
              placeholder="Search e.g. TCS"
              value={selected ? `${selected.trading_symbol} — ${selected.name}` : query}
              onChange={(e) => { setSelected(null); setQuery(e.target.value); }}
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
            <Input label="From date" type="date" required value={fromDate} onChange={(e) => setFromDate(e.target.value)} />
            <Input label="To date" type="date" required value={toDate} onChange={(e) => setToDate(e.target.value)} />
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div className="flex flex-col gap-1.5">
              <label className="text-sm font-medium text-ink/80 dark:text-paper/80">Segment</label>
              <select value={segment} onChange={(e) => setSegment(e.target.value)} className="rounded-md border border-ink/15 bg-white px-3 py-2 text-sm dark:border-paper/20 dark:bg-ink-soft">
                <option value="EQUITY_INTRADAY">Equity intraday</option>
                <option value="EQUITY_DELIVERY">Equity delivery</option>
                <option value="FUTURES">Futures</option>
                <option value="OPTIONS">Options</option>
              </select>
            </div>
            <Input label="Quantity" type="number" min={1} required value={quantity} onChange={(e) => setQuantity(e.target.value)} />
          </div>

          <Input label="Initial capital (₹)" type="number" min={1} required value={capital} onChange={(e) => setCapital(e.target.value)} />

          <div className="grid grid-cols-2 gap-4">
            <Input label="Entry threshold" type="number" step="0.1" min={-1} max={1} required value={entryThreshold} onChange={(e) => setEntryThreshold(e.target.value)} />
            <Input label="Exit threshold" type="number" step="0.1" min={-1} max={1} required value={exitThreshold} onChange={(e) => setExitThreshold(e.target.value)} />
          </div>
          <div className="grid grid-cols-2 gap-4">
            <Input label="Trailing stop (%)" type="number" step="0.5" min={0.5} required value={trailingStop} onChange={(e) => setTrailingStop(e.target.value)} />
            <Input label="Slippage (bps)" type="number" step="1" min={0} required value={slippage} onChange={(e) => setSlippage(e.target.value)} />
          </div>
          <p className="-mt-2 text-xs text-ink/50 dark:text-paper/50">
            Uses all five indicators at equal weight — per-indicator weighting isn't in this form yet (see strategies for that level of control).
          </p>

          {error && <p className="text-sm text-loss">{error}</p>}

          <Button type="submit" disabled={!selected || !name || running} className="w-full">
            {running ? "Running…" : "Run backtest"}
          </Button>
        </form>
      </Card>
    </div>
  );
}

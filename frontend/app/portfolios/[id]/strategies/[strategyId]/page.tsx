"use client";

import Link from "next/link";
import { useParams } from "next/navigation";
import { useEffect, useState } from "react";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { api, ApiError } from "@/lib/api";

type Strategy = {
  id: string;
  instrument: { id: string; trading_symbol: string; exchange: string };
  name: string;
  segment: string;
  quantity: number;
  is_active: boolean;
  rsi_weight: string;
  sma_crossover_weight: string;
  macd_weight: string;
  volume_spike_weight: string;
  momentum_weight: string;
  entry_score_threshold: string;
  exit_score_threshold: string;
  trailing_stop_pct: string;
  max_daily_loss: string;
  paused_until: string | null;
  current_watermark: string | null;
  last_evaluated_at: string | null;
};

type Order = {
  id: string;
  side: string;
  quantity: number;
  status: string;
  rejection_reason: string | null;
  placed_at: string;
};

type EvalResult = { signal: string; reason: string; order_id: string | null };

type WeightKey = "rsi_weight" | "sma_crossover_weight" | "macd_weight" | "volume_spike_weight" | "momentum_weight";

const WEIGHTS: [WeightKey, string][] = [
  ["rsi_weight", "RSI"],
  ["sma_crossover_weight", "SMA crossover"],
  ["macd_weight", "MACD"],
  ["volume_spike_weight", "Volume spike"],
  ["momentum_weight", "Momentum"],
];

export default function StrategyDetailPage() {
  const { id: portfolioId, strategyId } = useParams<{ id: string; strategyId: string }>();
  const [strategy, setStrategy] = useState<Strategy | null>(null);
  const [orders, setOrders] = useState<Order[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [evaluating, setEvaluating] = useState(false);
  const [evalResult, setEvalResult] = useState<EvalResult | null>(null);

  useEffect(() => {
    refresh();
  }, [portfolioId, strategyId]);

  async function refresh() {
    try {
      const [s, o] = await Promise.all([
        api.get<Strategy>(`/portfolios/${portfolioId}/strategies/${strategyId}`),
        api.get<Order[]>(`/portfolios/${portfolioId}/strategies/${strategyId}/orders`),
      ]);
      setStrategy(s);
      setOrders(o);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Could not load this strategy.");
    }
  }

  async function onToggleActive() {
    if (!strategy) return;
    try {
      await api.post(`/portfolios/${portfolioId}/strategies/${strategyId}/${strategy.is_active ? "deactivate" : "activate"}`);
      await refresh();
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Could not update strategy.");
    }
  }

  async function onEvaluateNow() {
    setEvaluating(true);
    setEvalResult(null);
    setError(null);
    try {
      const result = await api.post<EvalResult>(`/portfolios/${portfolioId}/strategies/${strategyId}/evaluate`);
      setEvalResult(result);
      await refresh();
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Evaluation failed.");
    } finally {
      setEvaluating(false);
    }
  }

  if (!strategy) return <div className="p-8 text-sm text-ink/60 dark:text-paper/60">{error || "Loading…"}</div>;

  return (
    <div className="mx-auto max-w-2xl p-8">
      <Link href={`/portfolios/${portfolioId}/strategies`} className="text-sm text-accent hover:underline">
        ← All strategies
      </Link>

      <div className="mt-2 flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-semibold">{strategy.name}</h1>
          <p className="text-sm text-ink/50 dark:text-paper/50">
            {strategy.instrument.trading_symbol} · {strategy.segment.replace("_", " ")} · qty {strategy.quantity}
          </p>
        </div>
        <span className={`rounded-full px-3 py-1 text-xs font-medium ${strategy.is_active ? "bg-gain/15 text-gain" : "bg-ink/10 text-ink/60 dark:bg-paper/10 dark:text-paper/60"}`}>
          {strategy.is_active ? "Active" : "Inactive"}
        </span>
      </div>

      {strategy.paused_until && (
        <p className="mt-2 text-sm text-caution">Paused until {strategy.paused_until} — today's daily loss limit was reached.</p>
      )}

      <div className="mt-6 flex gap-3">
        <Button onClick={onToggleActive}>{strategy.is_active ? "Deactivate" : "Activate"}</Button>
        <Button variant="ghost" onClick={onEvaluateNow} disabled={evaluating}>
          {evaluating ? "Evaluating…" : "Evaluate now"}
        </Button>
      </div>

      {evalResult && (
        <Card className="mt-4">
          <p className="text-sm font-medium">{evalResult.signal}</p>
          <p className="mt-1 text-sm text-ink/60 dark:text-paper/60">{evalResult.reason}</p>
        </Card>
      )}
      {error && <p className="mt-4 text-sm text-loss">{error}</p>}

      <Card className="mt-6">
        <h2 className="font-medium">Configuration</h2>
        <div className="mt-3 space-y-1 text-sm">
          {WEIGHTS.map(([key, label]) => (
            <div key={key} className="flex justify-between">
              <span className="text-ink/60 dark:text-paper/60">{label} weight</span>
              <span className="tabular">{strategy[key]}</span>
            </div>
          ))}
          <div className="flex justify-between border-t border-ink/10 pt-1 dark:border-paper/10">
            <span className="text-ink/60 dark:text-paper/60">Entry threshold</span>
            <span className="tabular">{strategy.entry_score_threshold}</span>
          </div>
          <div className="flex justify-between">
            <span className="text-ink/60 dark:text-paper/60">Exit threshold</span>
            <span className="tabular">{strategy.exit_score_threshold}</span>
          </div>
          <div className="flex justify-between">
            <span className="text-ink/60 dark:text-paper/60">Trailing stop</span>
            <span className="tabular">{strategy.trailing_stop_pct}%</span>
          </div>
          <div className="flex justify-between">
            <span className="text-ink/60 dark:text-paper/60">Max daily loss</span>
            <span className="tabular">₹{strategy.max_daily_loss}</span>
          </div>
          <div className="flex justify-between">
            <span className="text-ink/60 dark:text-paper/60">Trailing-stop watermark</span>
            <span className="tabular">{strategy.current_watermark ? `₹${strategy.current_watermark}` : "— (flat)"}</span>
          </div>
          <div className="flex justify-between">
            <span className="text-ink/60 dark:text-paper/60">Last evaluated</span>
            <span className="tabular">{strategy.last_evaluated_at ? new Date(strategy.last_evaluated_at).toLocaleString("en-IN") : "Never yet"}</span>
          </div>
        </div>
        <p className="mt-3 text-xs text-ink/40 dark:text-paper/40">
          Editing these values isn't in this UI yet — recreate the strategy to change its configuration.
        </p>
      </Card>

      <h2 className="mt-8 font-medium">Auto-trades from this strategy</h2>
      {orders.length === 0 ? (
        <p className="mt-2 text-sm text-ink/50 dark:text-paper/50">No trades yet.</p>
      ) : (
        <Card className="mt-2 overflow-x-auto p-0">
          <table className="tabular w-full text-sm">
            <thead className="border-b border-ink/10 text-left text-ink/50 dark:border-paper/10 dark:text-paper/50">
              <tr>
                <th className="px-4 py-2 font-normal">Side</th>
                <th className="px-4 py-2 font-normal">Qty</th>
                <th className="px-4 py-2 font-normal">Status</th>
                <th className="px-4 py-2 font-normal">When</th>
              </tr>
            </thead>
            <tbody>
              {orders.map((o) => (
                <tr key={o.id} className="border-b border-ink/5 last:border-0 dark:border-paper/5">
                  <td className={`px-4 py-2 font-sans ${o.side === "SELL" ? "text-loss" : "text-gain"}`}>{o.side}</td>
                  <td className="px-4 py-2">{o.quantity}</td>
                  <td className="px-4 py-2 font-sans" title={o.rejection_reason || undefined}>{o.status}</td>
                  <td className="px-4 py-2 font-sans">{new Date(o.placed_at).toLocaleString("en-IN")}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </Card>
      )}
    </div>
  );
}

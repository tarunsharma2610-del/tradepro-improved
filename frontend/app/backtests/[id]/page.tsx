"use client";

import Link from "next/link";
import { useParams } from "next/navigation";
import { useEffect, useState } from "react";
import { Card } from "@/components/ui/card";
import { api, ApiError } from "@/lib/api";

type Backtest = {
  id: string;
  instrument: { trading_symbol: string; exchange: string };
  name: string;
  from_date: string;
  to_date: string;
  initial_capital: string;
  quantity: number;
  status: string;
  error_message: string | null;
  final_capital: string | null;
  net_pnl: string | null;
  max_drawdown_pct: string | null;
  total_trades: number;
  win_count: number;
  loss_count: number;
  candles_evaluated: number;
};

type Trade = {
  side: string;
  quantity: number;
  price: string;
  gross_value: string;
  total_charges: string;
  realized_pnl: string;
  executed_at: string | null;
};

export default function BacktestDetailPage() {
  const { id } = useParams<{ id: string }>();
  const [backtest, setBacktest] = useState<Backtest | null>(null);
  const [trades, setTrades] = useState<Trade[]>([]);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    (async () => {
      try {
        const [b, t] = await Promise.all([
          api.get<Backtest>(`/backtests/${id}`),
          api.get<Trade[]>(`/backtests/${id}/trades`),
        ]);
        setBacktest(b);
        setTrades(t);
      } catch (err) {
        setError(err instanceof ApiError ? err.message : "Could not load this backtest.");
      }
    })();
  }, [id]);

  if (!backtest) return <div className="p-8 text-sm text-ink/60 dark:text-paper/60">{error || "Loading…"}</div>;

  const winRate = backtest.total_trades > 0 ? ((backtest.win_count / backtest.total_trades) * 100).toFixed(0) : null;

  return (
    <div className="mx-auto max-w-2xl p-8">
      <Link href="/backtests" className="text-sm text-accent hover:underline">
        ← All backtests
      </Link>
      <h1 className="mt-2 text-2xl font-semibold">{backtest.name}</h1>
      <p className="text-sm text-ink/50 dark:text-paper/50">
        {backtest.instrument.trading_symbol} · {backtest.from_date} → {backtest.to_date} · qty {backtest.quantity} ·
        started with ₹{Number(backtest.initial_capital).toLocaleString("en-IN")}
      </p>

      {backtest.status === "FAILED" && (
        <Card className="mt-6">
          <p className="text-sm text-loss">{backtest.error_message}</p>
        </Card>
      )}

      {backtest.status === "COMPLETED" && (
        <>
          <div className="mt-6 grid grid-cols-2 gap-4">
            <Card>
              <p className="text-xs text-ink/50 dark:text-paper/50">Net P&amp;L (after all costs)</p>
              <p className={`tabular mt-1 text-2xl font-semibold ${Number(backtest.net_pnl) >= 0 ? "text-gain" : "text-loss"}`}>
                {Number(backtest.net_pnl) >= 0 ? "+" : ""}₹{Number(backtest.net_pnl).toLocaleString("en-IN", { maximumFractionDigits: 2 })}
              </p>
            </Card>
            <Card>
              <p className="text-xs text-ink/50 dark:text-paper/50">Final capital</p>
              <p className="tabular mt-1 text-2xl font-semibold">₹{Number(backtest.final_capital).toLocaleString("en-IN", { maximumFractionDigits: 0 })}</p>
            </Card>
            <Card>
              <p className="text-xs text-ink/50 dark:text-paper/50">Trades (win / loss)</p>
              <p className="tabular mt-1 text-lg">
                {backtest.total_trades} <span className="text-ink/40 dark:text-paper/40">({backtest.win_count}W / {backtest.loss_count}L{winRate ? `, ${winRate}%` : ""})</span>
              </p>
            </Card>
            <Card>
              <p className="text-xs text-ink/50 dark:text-paper/50">Max drawdown</p>
              <p className="tabular mt-1 text-lg text-loss">{Number(backtest.max_drawdown_pct).toFixed(2)}%</p>
            </Card>
          </div>
          <p className="mt-3 text-xs text-ink/40 dark:text-paper/40">
            Evaluated {backtest.candles_evaluated} candles. Net P&amp;L already includes brokerage, STT, exchange
            charges, SEBI fees, stamp duty, GST, and simulated slippage on every fill.
          </p>
        </>
      )}

      {trades.length > 0 && (
        <>
          <h2 className="mt-8 font-medium">Trade log</h2>
          <Card className="mt-2 overflow-x-auto p-0">
            <table className="tabular w-full text-sm">
              <thead className="border-b border-ink/10 text-left text-ink/50 dark:border-paper/10 dark:text-paper/50">
                <tr>
                  <th className="px-4 py-2 font-normal">Side</th>
                  <th className="px-4 py-2 font-normal">Qty</th>
                  <th className="px-4 py-2 font-normal">Price</th>
                  <th className="px-4 py-2 font-normal">Costs</th>
                  <th className="px-4 py-2 font-normal">P&amp;L</th>
                </tr>
              </thead>
              <tbody>
                {trades.map((t, i) => (
                  <tr key={i} className="border-b border-ink/5 last:border-0 dark:border-paper/5">
                    <td className={`px-4 py-2 font-sans ${t.side === "SELL" ? "text-loss" : "text-gain"}`}>{t.side}</td>
                    <td className="px-4 py-2">{t.quantity}</td>
                    <td className="px-4 py-2">₹{Number(t.price).toFixed(2)}</td>
                    <td className="px-4 py-2 text-ink/50 dark:text-paper/50">₹{Number(t.total_charges).toFixed(2)}</td>
                    <td className={`px-4 py-2 ${Number(t.realized_pnl) < 0 ? "text-loss" : Number(t.realized_pnl) > 0 ? "text-gain" : "text-ink/40 dark:text-paper/40"}`}>
                      {Number(t.realized_pnl) !== 0 ? `₹${Number(t.realized_pnl).toFixed(2)}` : "—"}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </Card>
        </>
      )}
    </div>
  );
}

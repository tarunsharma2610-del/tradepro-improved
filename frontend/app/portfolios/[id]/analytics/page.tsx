"use client";

import Link from "next/link";
import { useParams } from "next/navigation";
import { useEffect, useState } from "react";
import { Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { Card } from "@/components/ui/card";
import { api, ApiError } from "@/lib/api";

type EquityPoint = { timestamp: string; cash_balance: string };
type PortfolioAnalytics = {
  total_realized_pnl: string;
  total_trades: number;
  win_count: number;
  loss_count: number;
  win_rate_pct: string | null;
  best_trade_pnl: string | null;
  worst_trade_pnl: string | null;
  total_costs_paid: string;
  equity_curve: EquityPoint[];
  equity_curve_note: string;
};
type StrategyAnalytics = {
  strategy_id: string;
  strategy_name: string;
  is_active: boolean;
  total_trades: number;
  win_count: number;
  loss_count: number;
  total_realized_pnl: string;
};

export default function PortfolioAnalyticsPage() {
  const { id } = useParams<{ id: string }>();
  const [analytics, setAnalytics] = useState<PortfolioAnalytics | null>(null);
  const [strategies, setStrategies] = useState<StrategyAnalytics[]>([]);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    (async () => {
      try {
        const [a, s] = await Promise.all([
          api.get<PortfolioAnalytics>(`/portfolios/${id}/analytics`),
          api.get<StrategyAnalytics[]>(`/portfolios/${id}/strategies/analytics`),
        ]);
        setAnalytics(a);
        setStrategies(s);
      } catch (err) {
        setError(err instanceof ApiError ? err.message : "Could not load analytics.");
      }
    })();
  }, [id]);

  if (!analytics) return <div className="p-8 text-sm text-ink/60 dark:text-paper/60">{error || "Loading…"}</div>;

  const chartData = analytics.equity_curve.map((p) => ({
    time: new Date(p.timestamp).toLocaleDateString("en-IN", { month: "short", day: "numeric" }),
    cash: Number(p.cash_balance),
  }));
  const pnlPositive = Number(analytics.total_realized_pnl) >= 0;

  return (
    <div className="mx-auto max-w-2xl p-8">
      <Link href={`/portfolios/${id}`} className="text-sm text-accent hover:underline">
        ← Portfolio
      </Link>
      <h1 className="mt-2 text-2xl font-semibold">Analytics</h1>

      <div className="mt-6 grid grid-cols-2 gap-4">
        <Card>
          <p className="text-xs text-ink/50 dark:text-paper/50">Total realized P&amp;L</p>
          <p className={`tabular mt-1 text-2xl font-semibold ${pnlPositive ? "text-gain" : "text-loss"}`}>
            {pnlPositive ? "+" : ""}₹{Number(analytics.total_realized_pnl).toLocaleString("en-IN", { maximumFractionDigits: 2 })}
          </p>
        </Card>
        <Card>
          <p className="text-xs text-ink/50 dark:text-paper/50">Win rate</p>
          <p className="tabular mt-1 text-2xl font-semibold">
            {analytics.win_rate_pct ? `${Number(analytics.win_rate_pct).toFixed(0)}%` : "—"}
          </p>
          <p className="text-xs text-ink/40 dark:text-paper/40">{analytics.win_count}W / {analytics.loss_count}L of {analytics.total_trades}</p>
        </Card>
        <Card>
          <p className="text-xs text-ink/50 dark:text-paper/50">Best / worst trade</p>
          <p className="tabular mt-1 text-sm">
            <span className="text-gain">{analytics.best_trade_pnl ? `+₹${Number(analytics.best_trade_pnl).toFixed(0)}` : "—"}</span>
            {" / "}
            <span className="text-loss">{analytics.worst_trade_pnl ? `₹${Number(analytics.worst_trade_pnl).toFixed(0)}` : "—"}</span>
          </p>
        </Card>
        <Card>
          <p className="text-xs text-ink/50 dark:text-paper/50">Total costs paid</p>
          <p className="tabular mt-1 text-lg">₹{Number(analytics.total_costs_paid).toLocaleString("en-IN", { maximumFractionDigits: 2 })}</p>
        </Card>
      </div>

      {chartData.length > 1 && (
        <Card className="mt-6">
          <p className="mb-3 text-sm font-medium">Cash balance over time</p>
          <div className="h-56 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={chartData}>
                <XAxis dataKey="time" tick={{ fontSize: 11 }} stroke="currentColor" opacity={0.4} />
                <YAxis tick={{ fontSize: 11 }} stroke="currentColor" opacity={0.4} tickFormatter={(v) => `₹${(v / 1000).toFixed(0)}k`} />
                <Tooltip formatter={(v) => [`₹${Number(v).toLocaleString("en-IN")}`, "Cash"]} />
                <Line type="monotone" dataKey="cash" stroke="#2F6FEB" strokeWidth={2} dot={false} />
              </LineChart>
            </ResponsiveContainer>
          </div>
          <p className="mt-2 text-xs text-ink/40 dark:text-paper/40">{analytics.equity_curve_note}</p>
        </Card>
      )}

      {strategies.length > 0 && (
        <>
          <h2 className="mt-8 font-medium">Strategy comparison</h2>
          <Card className="mt-2 overflow-x-auto p-0">
            <table className="tabular w-full text-sm">
              <thead className="border-b border-ink/10 text-left text-ink/50 dark:border-paper/10 dark:text-paper/50">
                <tr>
                  <th className="px-4 py-2 font-normal">Strategy</th>
                  <th className="px-4 py-2 font-normal">Trades</th>
                  <th className="px-4 py-2 font-normal">P&amp;L</th>
                </tr>
              </thead>
              <tbody>
                {strategies.map((s) => (
                  <tr key={s.strategy_id} className="border-b border-ink/5 last:border-0 dark:border-paper/5">
                    <td className="px-4 py-2 font-sans">
                      {s.strategy_name} {!s.is_active && <span className="text-ink/30 dark:text-paper/30">(inactive)</span>}
                    </td>
                    <td className="px-4 py-2">{s.total_trades} ({s.win_count}W/{s.loss_count}L)</td>
                    <td className={`px-4 py-2 ${Number(s.total_realized_pnl) < 0 ? "text-loss" : Number(s.total_realized_pnl) > 0 ? "text-gain" : ""}`}>
                      ₹{Number(s.total_realized_pnl).toFixed(2)}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </Card>
        </>
      )}

      {error && <p className="mt-4 text-sm text-loss">{error}</p>}
    </div>
  );
}

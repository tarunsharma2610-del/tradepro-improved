"use client";

import Link from "next/link";
import { useParams } from "next/navigation";
import { useEffect, useState } from "react";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { api, ApiError } from "@/lib/api";

type Portfolio = {
  id: string; name: string; virtual_capital: string; cash_balance: string;
  risk_controls_enabled: boolean; max_daily_loss: string | null; max_open_exposure: string | null;
  max_order_value: string | null; max_open_positions: number | null; max_orders_per_day: number | null;
};
type RiskSettings = {
  name: string; risk_controls_enabled: boolean; max_daily_loss: string; max_open_exposure: string;
  max_order_value: string; max_open_positions: string; max_orders_per_day: string;
};
type InstrumentBrief = { id: string; trading_symbol: string; exchange: string };
type Instrument = InstrumentBrief & { instrument_key: string; name: string; segment: string };
type StreamStatus = { running: boolean; connected: boolean; instrument_count?: number; quotes: Record<string, { ltp: number; received_at: string; stale: boolean } | null> };
type Position = { instrument: InstrumentBrief; quantity: number; avg_price: string; realized_pnl: string };
type Order = {
  id: string;
  instrument: InstrumentBrief;
  side: string;
  order_type: string;
  segment: string;
  quantity: number;
  limit_price: string | null;
  status: string;
  rejection_reason: string | null;
  placed_at: string;
};

const SEGMENTS = ["EQUITY_DELIVERY", "EQUITY_INTRADAY", "FUTURES", "OPTIONS"];

export default function PortfolioDetailPage() {
  const { id } = useParams<{ id: string }>();
  const [portfolio, setPortfolio] = useState<Portfolio | null>(null);
  const [positions, setPositions] = useState<Position[]>([]);
  const [orders, setOrders] = useState<Order[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [riskSettings, setRiskSettings] = useState<RiskSettings>({
    name: "", risk_controls_enabled: false, max_daily_loss: "", max_open_exposure: "",
    max_order_value: "", max_open_positions: "", max_orders_per_day: "",
  });
  const [savingRisk, setSavingRisk] = useState(false);
  const [riskMessage, setRiskMessage] = useState<string | null>(null);
  const [streamActive, setStreamActive] = useState(false);
  const [streamStatus, setStreamStatus] = useState<StreamStatus | null>(null);
  const [streamError, setStreamError] = useState<string | null>(null);

  const [query, setQuery] = useState("");
  const [results, setResults] = useState<Instrument[]>([]);
  const [selected, setSelected] = useState<Instrument | null>(null);
  const [side, setSide] = useState("BUY");
  const [segment, setSegment] = useState("EQUITY_DELIVERY");
  const [orderType, setOrderType] = useState<"MARKET" | "LIMIT">("MARKET");
  const [quantity, setQuantity] = useState("1");
  const [limitPrice, setLimitPrice] = useState("");
  const [placing, setPlacing] = useState(false);
  const [cancellingOrder, setCancellingOrder] = useState<string | null>(null);
  const [lastResult, setLastResult] = useState<Order | null>(null);

  const [question, setQuestion] = useState("");
  const [answer, setAnswer] = useState<string | null>(null);
  const [asking, setAsking] = useState(false);
  const [assistantError, setAssistantError] = useState<string | null>(null);

  useEffect(() => {
    refresh();
  }, [id]);

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
      const [p, pos, ord] = await Promise.all([
        api.get<Portfolio>(`/portfolios/${id}`),
        api.get<Position[]>(`/portfolios/${id}/positions`),
        api.get<Order[]>(`/portfolios/${id}/orders`),
      ]);
      setPortfolio(p);
      setRiskSettings({
        name: p.name,
        risk_controls_enabled: p.risk_controls_enabled ?? false,
        max_daily_loss: p.max_daily_loss ?? "",
        max_open_exposure: p.max_open_exposure ?? "",
        max_order_value: p.max_order_value ?? "",
        max_open_positions: p.max_open_positions == null ? "" : String(p.max_open_positions),
        max_orders_per_day: p.max_orders_per_day == null ? "" : String(p.max_orders_per_day),
      });
      setPositions(pos);
      setOrders(ord);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Could not load this portfolio.");
    }
  }

  useEffect(() => {
    if (!streamActive || !selected) return;
    let cancelled = false;
    const poll = async () => {
      try {
        const result = await api.get<StreamStatus>("/market-data/stream");
        if (!cancelled) setStreamStatus(result);
      } catch (err) {
        if (!cancelled) setStreamError(err instanceof ApiError ? err.message : "Could not read stream status.");
      }
    };
    void poll();
    const handle = setInterval(() => void poll(), 2500);
    return () => {
      cancelled = true;
      clearInterval(handle);
    };
  }, [streamActive, selected]);

  async function onStartStream() {
    if (!selected) return;
    setStreamError(null);
    try {
      await api.post("/market-data/stream", { instrument_keys: [selected.instrument_key] });
      setStreamActive(true);
    } catch (err) {
      setStreamError(err instanceof ApiError ? err.message : "Could not start market stream.");
    }
  }

  async function onStopStream() {
    setStreamError(null);
    try {
      await api.del("/market-data/stream");
      setStreamActive(false);
      setStreamStatus(null);
    } catch (err) {
      setStreamError(err instanceof ApiError ? err.message : "Could not stop market stream.");
    }
  }

  async function onSaveRiskSettings(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    setRiskMessage(null);
    setSavingRisk(true);
    const numberOrNull = (value: string) => value.trim() === "" ? null : Number(value);
    try {
      const updated = await api.patch<Portfolio>(`/portfolios/${id}/risk-settings`, {
        name: riskSettings.name,
        risk_controls_enabled: riskSettings.risk_controls_enabled,
        max_daily_loss: numberOrNull(riskSettings.max_daily_loss),
        max_open_exposure: numberOrNull(riskSettings.max_open_exposure),
        max_order_value: numberOrNull(riskSettings.max_order_value),
        max_open_positions: numberOrNull(riskSettings.max_open_positions),
        max_orders_per_day: numberOrNull(riskSettings.max_orders_per_day),
      });
      setPortfolio(updated);
      setRiskMessage("Portfolio risk settings saved.");
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Could not save portfolio risk settings.");
    } finally {
      setSavingRisk(false);
    }
  }

  async function onPlaceOrder(e: React.FormEvent) {
    e.preventDefault();
    if (!selected) return;
    setError(null);
    setLastResult(null);
    setPlacing(true);
    try {
      const order = await api.post<Order>(`/portfolios/${id}/orders`, {
        instrument_id: selected.id,
        side,
        order_type: orderType,
        segment,
        quantity: Number(quantity),
        limit_price: orderType === "LIMIT" ? limitPrice : undefined,
      });
      setLastResult(order);
      await refresh();
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Could not place the order.");
    } finally {
      setPlacing(false);
    }
  }

  async function onCancelOrder(orderId: string) {
    setError(null);
    setCancellingOrder(orderId);
    try {
      await api.del<Order>(`/portfolios/${id}/orders/${orderId}`);
      await refresh();
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Could not cancel this order.");
    } finally {
      setCancellingOrder(null);
    }
  }

  async function onAsk(e: React.FormEvent) {
    e.preventDefault();
    setAssistantError(null);
    setAnswer(null);
    setAsking(true);
    try {
      const result = await api.post<{ answer: string }>(`/portfolios/${id}/assistant/ask`, { question });
      setAnswer(result.answer);
    } catch (err) {
      setAssistantError(err instanceof ApiError ? err.message : "Could not reach the assistant.");
    } finally {
      setAsking(false);
    }
  }

  if (!portfolio) return <div className="p-8 text-sm text-ink/60 dark:text-paper/60">{error || "Loading…"}</div>;

  return (
    <div className="mx-auto max-w-3xl p-8">
      <Link href="/portfolios" className="text-sm text-accent hover:underline">
        ← All portfolios
      </Link>
      <div className="mt-2 flex items-baseline justify-between">
        <h1 className="text-2xl font-semibold">{portfolio.name}</h1>
        <p className="tabular text-xl">₹{Number(portfolio.cash_balance).toLocaleString("en-IN", { maximumFractionDigits: 2 })}</p>
      </div>
      <div className="flex items-center justify-between">
        <p className="text-sm text-ink/50 dark:text-paper/50">
          Cash balance · started with ₹{Number(portfolio.virtual_capital).toLocaleString("en-IN")}
        </p>
        <div className="flex gap-4">
          <Link href={`/portfolios/${id}/analytics`} className="text-sm text-accent hover:underline">
            Analytics
          </Link>
          <Link href={`/portfolios/${id}/strategies`} className="text-sm text-accent hover:underline">
            Strategies (auto-trading) →
          </Link>
        </div>
      </div>

      <Card className="mt-6">
        <form onSubmit={onSaveRiskSettings} className="space-y-4">
          <div>
            <h2 className="font-medium">Portfolio & risk settings</h2>
            <p className="mt-1 text-xs text-ink/50 dark:text-paper/50">
              Configure optional limits for this portfolio. Limits are disabled by default. Amounts are in INR;
              exposure is an estimate based on open position cost, not broker margin.
            </p>
          </div>
          <Input label="Portfolio name" required value={riskSettings.name} onChange={(e) => setRiskSettings({ ...riskSettings, name: e.target.value })} />
          <label className="flex items-center gap-2 text-sm">
            <input
              type="checkbox"
              checked={riskSettings.risk_controls_enabled}
              onChange={(e) => setRiskSettings({ ...riskSettings, risk_controls_enabled: e.target.checked })}
            />
            Enable portfolio risk controls
          </label>
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
            <Input label="Maximum daily realized loss (₹)" type="number" min="0.01" step="0.01" value={riskSettings.max_daily_loss} onChange={(e) => setRiskSettings({ ...riskSettings, max_daily_loss: e.target.value })} />
            <Input label="Maximum estimated open exposure (₹)" type="number" min="0.01" step="0.01" value={riskSettings.max_open_exposure} onChange={(e) => setRiskSettings({ ...riskSettings, max_open_exposure: e.target.value })} />
            <Input label="Maximum order value (₹)" type="number" min="0.01" step="0.01" value={riskSettings.max_order_value} onChange={(e) => setRiskSettings({ ...riskSettings, max_order_value: e.target.value })} />
            <Input label="Maximum simultaneous open positions" type="number" min="1" step="1" value={riskSettings.max_open_positions} onChange={(e) => setRiskSettings({ ...riskSettings, max_open_positions: e.target.value })} />
            <Input label="Maximum orders per day" type="number" min="1" step="1" value={riskSettings.max_orders_per_day} onChange={(e) => setRiskSettings({ ...riskSettings, max_orders_per_day: e.target.value })} />
          </div>
          {riskSettings.risk_controls_enabled && (
            <p className="text-xs text-caution">At least one limit is required. Risk-reducing orders that close an existing position remain allowed.</p>
          )}
          {riskMessage && <p className="text-sm text-gain">{riskMessage}</p>}
          <Button type="submit" disabled={savingRisk}>{savingRisk ? "Saving…" : "Save portfolio settings"}</Button>
        </form>
      </Card>

      {/* Order entry */}
      <Card className="mt-6">
        <form onSubmit={onPlaceOrder} className="space-y-4">
          <h2 className="font-medium">Place a paper order</h2>

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
                  <li
                    key={r.id}
                    className="cursor-pointer px-3 py-2 text-sm hover:bg-accent/10"
                    onClick={() => {
                      setSelected(r);
                      setResults([]);
                    }}
                  >
                    <span className="font-medium">{r.trading_symbol}</span>{" "}
                    <span className="text-ink/50 dark:text-paper/50">{r.name}</span>
                  </li>
                ))}
              </ul>
            )}
          </div>

          {selected && (
            <div className="space-y-2 rounded-md border border-ink/10 p-3 dark:border-paper/10">
              <div className="flex flex-wrap items-center gap-2">
                <Button type="button" variant="ghost" onClick={() => void onStartStream()}>
                  {streamActive ? "Restart stream for selected instrument" : "Start live price stream"}
                </Button>
                {streamActive && <Button type="button" variant="ghost" onClick={() => void onStopStream()}>Stop stream</Button>}
                <span className="text-xs text-ink/50 dark:text-paper/50">
                  {streamStatus?.connected ? "Connected" : streamActive ? "Connecting…" : "Not streaming"}
                </span>
              </div>
              {streamStatus?.quotes?.[selected.instrument_key] && (
                <p className="text-sm">
                  Live LTP: <strong>₹{streamStatus.quotes[selected.instrument_key]!.ltp.toFixed(2)}</strong>
                  <span className="ml-2 text-xs text-ink/50 dark:text-paper/50">
                    Updated {new Date(streamStatus.quotes[selected.instrument_key]!.received_at).toLocaleTimeString()}
                  </span>
                </p>
              )}
              <p className="text-xs text-ink/50 dark:text-paper/50">
                This user-level stream subscription is replaced when you start a stream for another instrument. Stale quotes are hidden.
              </p>
              {streamError && <p className="text-sm text-loss">{streamError}</p>}
            </div>
          )}

          <div className="grid grid-cols-2 gap-4">
            <div className="flex flex-col gap-1.5">
              <label className="text-sm font-medium text-ink/80 dark:text-paper/80">Side</label>
              <select value={side} onChange={(e) => setSide(e.target.value)} className="rounded-md border border-ink/15 bg-white px-3 py-2 text-sm dark:border-paper/20 dark:bg-ink-soft">
                <option value="BUY">Buy</option>
                <option value="SELL">Sell</option>
              </select>
            </div>
            <div className="flex flex-col gap-1.5">
              <label className="text-sm font-medium text-ink/80 dark:text-paper/80">Segment</label>
              <select value={segment} onChange={(e) => setSegment(e.target.value)} className="rounded-md border border-ink/15 bg-white px-3 py-2 text-sm dark:border-paper/20 dark:bg-ink-soft">
                {SEGMENTS.map((s) => (
                  <option key={s} value={s}>
                    {s.replace("_", " ")}
                  </option>
                ))}
              </select>
            </div>
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div className="flex flex-col gap-1.5">
              <label className="text-sm font-medium text-ink/80 dark:text-paper/80">Order type</label>
              <select value={orderType} onChange={(e) => setOrderType(e.target.value as "MARKET" | "LIMIT")} className="rounded-md border border-ink/15 bg-white px-3 py-2 text-sm dark:border-paper/20 dark:bg-ink-soft">
                <option value="MARKET">Market</option>
                <option value="LIMIT">Limit</option>
              </select>
            </div>
            <Input label="Quantity" type="number" min={1} required value={quantity} onChange={(e) => setQuantity(e.target.value)} />
          </div>

          {orderType === "LIMIT" && (
            <>
              <Input label="Limit price (₹)" type="number" min={0.01} step="any" required value={limitPrice} onChange={(e) => setLimitPrice(e.target.value)} />
              <p className="-mt-2 text-xs text-caution">
                Pending limit orders are checked by the worker during market hours (about every 5 minutes). They fill only when the quote crosses your limit; if a quote is unavailable, they remain pending.
              </p>
            </>
          )}

          {orderType === "MARKET" && (
            <p className="text-xs text-ink/50 dark:text-paper/50">
              Fills instantly at the live price from your connected broker. No broker connected yet? The order will be
              rejected with a clear reason instead of guessing a price —{" "}
              <Link href="/settings/broker" className="text-accent hover:underline">
                connect one
              </Link>
              .
            </p>
          )}

          {error && <p className="text-sm text-loss">{error}</p>}
          {lastResult && (
            <p className={lastResult.status === "FILLED" ? "text-sm text-gain" : "text-sm text-caution"}>
              {lastResult.status === "FILLED"
                ? `Filled: ${lastResult.side} ${lastResult.quantity} ${lastResult.instrument.trading_symbol}.`
                : `${lastResult.status}: ${lastResult.rejection_reason || "See order history."}`}
            </p>
          )}

          <Button type="submit" disabled={!selected || placing} className="w-full">
            {placing ? "Placing…" : "Place order"}
          </Button>
        </form>
      </Card>

      {/* Positions */}
      <h2 className="mt-8 font-medium">Positions</h2>
      {positions.length === 0 ? (
        <p className="mt-2 text-sm text-ink/50 dark:text-paper/50">No open positions yet.</p>
      ) : (
        <Card className="mt-2 overflow-x-auto p-0">
          <table className="tabular w-full text-sm">
            <thead className="border-b border-ink/10 text-left text-ink/50 dark:border-paper/10 dark:text-paper/50">
              <tr>
                <th className="px-4 py-2 font-normal">Symbol</th>
                <th className="px-4 py-2 font-normal">Qty</th>
                <th className="px-4 py-2 font-normal">Avg price</th>
                <th className="px-4 py-2 font-normal">Realized P&amp;L</th>
              </tr>
            </thead>
            <tbody>
              {positions.map((p) => (
                <tr key={p.instrument.id} className="border-b border-ink/5 last:border-0 dark:border-paper/5">
                  <td className="px-4 py-2 font-sans">{p.instrument.trading_symbol}</td>
                  <td className={`px-4 py-2 ${p.quantity < 0 ? "text-loss" : ""}`}>{p.quantity}</td>
                  <td className="px-4 py-2">₹{Number(p.avg_price).toFixed(2)}</td>
                  <td className={`px-4 py-2 ${Number(p.realized_pnl) < 0 ? "text-loss" : Number(p.realized_pnl) > 0 ? "text-gain" : ""}`}>
                    ₹{Number(p.realized_pnl).toFixed(2)}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </Card>
      )}

      {/* Order history */}
      <h2 className="mt-8 font-medium">Recent orders</h2>
      {orders.length === 0 ? (
        <p className="mt-2 text-sm text-ink/50 dark:text-paper/50">No orders yet.</p>
      ) : (
        <Card className="mt-2 overflow-x-auto p-0">
          <table className="tabular w-full text-sm">
            <thead className="border-b border-ink/10 text-left text-ink/50 dark:border-paper/10 dark:text-paper/50">
              <tr>
                <th className="px-4 py-2 font-normal">Symbol</th>
                <th className="px-4 py-2 font-normal">Side</th>
                <th className="px-4 py-2 font-normal">Type / limit</th>
                <th className="px-4 py-2 font-normal">Qty</th>
                <th className="px-4 py-2 font-normal">Status</th>
                <th className="px-4 py-2 font-normal">Action</th>
              </tr>
            </thead>
            <tbody>
              {orders.map((o) => (
                <tr key={o.id} className="border-b border-ink/5 last:border-0 dark:border-paper/5">
                  <td className="px-4 py-2 font-sans">{o.instrument.trading_symbol}</td>
                  <td className={`px-4 py-2 ${o.side === "SELL" ? "text-loss" : "text-gain"}`}>{o.side}</td>
                  <td className="px-4 py-2">{o.order_type}{o.order_type === "LIMIT" && o.limit_price ? ` · ₹${Number(o.limit_price).toFixed(2)}` : ""}</td>
                  <td className="px-4 py-2">{o.quantity}</td>
                  <td className="px-4 py-2 font-sans" title={o.rejection_reason || undefined}>
                    {o.status}
                  </td>
                  <td className="px-4 py-2">
                    {o.status === "PENDING" && (
                      <Button variant="ghost" disabled={cancellingOrder === o.id} onClick={() => void onCancelOrder(o.id)}>
                        {cancellingOrder === o.id ? "Cancelling…" : "Cancel"}
                      </Button>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </Card>
      )}

      {/* AI assistant */}
      <h2 className="mt-8 font-medium">Ask about this portfolio</h2>
      <Card className="mt-2">
        <form onSubmit={onAsk} className="space-y-3">
          <Input
            label="Question"
            placeholder="e.g. What's my biggest position? Any recent news on it?"
            required
            value={question}
            onChange={(e) => setQuestion(e.target.value)}
          />
          <p className="-mt-1 text-xs text-ink/50 dark:text-paper/50">
            Answers are grounded only in this portfolio's real positions, orders, and tagged news — never live prices
            or invented figures.
          </p>
          {assistantError && <p className="text-sm text-loss">{assistantError}</p>}
          <Button type="submit" disabled={asking || !question}>
            {asking ? "Asking…" : "Ask"}
          </Button>
        </form>
        {answer && (
          <div className="mt-4 whitespace-pre-wrap border-t border-ink/10 pt-4 text-sm dark:border-paper/10">{answer}</div>
        )}
      </Card>
    </div>
  );
}

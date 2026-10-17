"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { ApiError, api } from "@/lib/api";

type Portfolio = {
  id: string;
  name: string;
  virtual_capital: string;
  cash_balance: string;
};

type BrokerConnection = {
  id: string;
  broker: string;
  api_key_masked: string;
  is_connected: boolean;
  last_connected_at: string | null;
  last_error: string | null;
};

const navigation = [
  { href: "/portfolios", title: "Portfolios", description: "Manage virtual capital, positions, orders and P&L." },
  { href: "/backtests", title: "Strategy backtests", description: "Test a strategy on historical market data before using it." },
  { href: "/news", title: "Market news", description: "Review collected market news and related instruments." },
  { href: "/settings/broker", title: "Broker connection", description: "Connect and test your Upstox session." },
  { href: "/reconciliation", title: "Reconciliation review", description: "Review read-only broker reconciliation runs and manual-review issues." },
  { href: "/settings/notifications", title: "Notifications", description: "Configure Telegram and WhatsApp notifications." },
];

function inr(value: number) {
  return new Intl.NumberFormat("en-IN", {
    style: "currency",
    currency: "INR",
    maximumFractionDigits: 0,
  }).format(value);
}

export default function DashboardPage() {
  const [portfolios, setPortfolios] = useState<Portfolio[]>([]);
  const [connections, setConnections] = useState<BrokerConnection[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [needsLogin, setNeedsLogin] = useState(false);

  useEffect(() => {
    let active = true;

    async function loadDashboard() {
      setLoading(true);
      setError(null);
      try {
        const [portfolioList, brokerList] = await Promise.all([
          api.get<Portfolio[]>("/portfolios"),
          api.get<BrokerConnection[]>("/settings/broker"),
        ]);
        if (!active) return;
        setPortfolios(portfolioList);
        setConnections(brokerList);
      } catch (err) {
        if (!active) return;
        if (err instanceof ApiError && err.status === 401) {
          setNeedsLogin(true);
          setError("Please log in to view your trading dashboard.");
        } else {
          setError(err instanceof ApiError ? err.message : "Could not load your dashboard.");
        }
      } finally {
        if (active) setLoading(false);
      }
    }

    void loadDashboard();
    return () => {
      active = false;
    };
  }, []);

  const startingCapital = portfolios.reduce((sum, p) => sum + Number(p.virtual_capital || 0), 0);
  const availableCash = portfolios.reduce((sum, p) => sum + Number(p.cash_balance || 0), 0);
  const connectedBrokers = connections.filter((connection) => connection.is_connected).length;

  return (
    <main className="mx-auto max-w-6xl space-y-8 p-6 sm:p-8">
      <header className="flex flex-col gap-4 sm:flex-row sm:items-end sm:justify-between">
        <div>
          <p className="text-sm font-medium uppercase tracking-wide text-accent">Tradepro</p>
          <h1 className="mt-1 text-3xl font-semibold">Trading dashboard</h1>
          <p className="mt-2 max-w-2xl text-sm text-ink/60 dark:text-paper/60">
            A single place to review your paper-trading portfolios, backtests and broker connection.
            Live trading is not enabled by this dashboard.
          </p>
        </div>
        <div className="flex flex-wrap gap-2">
          <Link href="/portfolios"><Button>Open portfolios</Button></Link>
          <Link href="/settings/broker"><Button variant="ghost">Broker settings</Button></Link>
        </div>
      </header>

      {error && (
        <Card className="border-loss/30">
          <p className="text-sm text-loss">{error}</p>
          {needsLogin && <div className="mt-3"><Link href="/login"><Button>Go to login</Button></Link></div>}
        </Card>
      )}

      <section aria-label="Account summary" className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <Card>
          <p className="text-sm text-ink/60 dark:text-paper/60">Portfolios</p>
          <p className="mt-2 text-2xl font-semibold tabular">{loading ? "—" : portfolios.length}</p>
        </Card>
        <Card>
          <p className="text-sm text-ink/60 dark:text-paper/60">Starting virtual capital</p>
          <p className="mt-2 text-2xl font-semibold tabular">{loading ? "—" : inr(startingCapital)}</p>
        </Card>
        <Card>
          <p className="text-sm text-ink/60 dark:text-paper/60">Available virtual cash</p>
          <p className="mt-2 text-2xl font-semibold tabular">{loading ? "—" : inr(availableCash)}</p>
        </Card>
        <Card>
          <p className="text-sm text-ink/60 dark:text-paper/60">Connected brokers</p>
          <p className="mt-2 text-2xl font-semibold tabular">
            {loading ? "—" : `${connectedBrokers} / ${connections.length}`}
          </p>
          <p className="mt-1 text-xs text-ink/50 dark:text-paper/50">Connection status only; not a live-trading indicator.</p>
        </Card>
      </section>

      <section>
        <div className="mb-3">
          <h2 className="text-xl font-semibold">Workspace</h2>
          <p className="mt-1 text-sm text-ink/60 dark:text-paper/60">Open a section to continue.</p>
        </div>
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
          {navigation.map((item) => (
            <Link key={item.href} href={item.href} className="block">
              <Card className="h-full transition-colors hover:border-accent">
                <h3 className="font-medium">{item.title}</h3>
                <p className="mt-2 text-sm text-ink/60 dark:text-paper/60">{item.description}</p>
                <p className="mt-4 text-sm font-medium text-accent">Open section →</p>
              </Card>
            </Link>
          ))}
        </div>
      </section>

      <section>
        <h2 className="text-xl font-semibold">Paper-trading safety</h2>
        <Card className="mt-3">
          <p className="text-sm text-ink/70 dark:text-paper/70">
            Market orders in the current implementation simulate fills using the broker&apos;s latest price.
            Limit orders remain pending until a limit-order matcher is implemented. Verify orders and positions
            before relying on results; do not use this application for live orders yet.
          </p>
        </Card>
      </section>
    </main>
  );
}

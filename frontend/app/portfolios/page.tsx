"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { api, ApiError } from "@/lib/api";

type Portfolio = {
  id: string;
  name: string;
  virtual_capital: string;
  cash_balance: string;
};

export default function PortfoliosPage() {
  const [portfolios, setPortfolios] = useState<Portfolio[]>([]);
  const [name, setName] = useState("");
  const [capital, setCapital] = useState("100000");
  const [creating, setCreating] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    refresh();
  }, []);

  async function refresh() {
    try {
      setPortfolios(await api.get<Portfolio[]>("/portfolios"));
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Could not load portfolios.");
    }
  }

  async function onCreate(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    setCreating(true);
    try {
      await api.post("/portfolios", { name, virtual_capital: capital });
      setName("");
      await refresh();
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Could not create portfolio.");
    } finally {
      setCreating(false);
    }
  }

  return (
    <div className="mx-auto max-w-2xl p-8">
      <h1 className="text-2xl font-semibold">Portfolios</h1>
      <p className="mt-1 text-sm text-ink/60 dark:text-paper/60">
        Each portfolio has its own virtual capital and P&amp;L — trades in one never affect another.
      </p>

      {portfolios.length > 0 && (
        <div className="mt-6 space-y-3">
          {portfolios.map((p) => (
            <Link key={p.id} href={`/portfolios/${p.id}`}>
              <Card className="flex items-center justify-between hover:border-accent">
                <div>
                  <p className="font-medium">{p.name}</p>
                  <p className="tabular text-sm text-ink/50 dark:text-paper/50">
                    Started with ₹{Number(p.virtual_capital).toLocaleString("en-IN")}
                  </p>
                </div>
                <p className="tabular text-lg">
                  ₹{Number(p.cash_balance).toLocaleString("en-IN", { maximumFractionDigits: 0 })}
                </p>
              </Card>
            </Link>
          ))}
        </div>
      )}

      <Card className="mt-6">
        <form onSubmit={onCreate} className="space-y-4">
          <h2 className="font-medium">New portfolio</h2>
          <Input label="Name" required value={name} onChange={(e) => setName(e.target.value)} placeholder="e.g. Intraday testing" />
          <Input
            label="Virtual capital (₹)"
            type="number"
            required
            min={1}
            value={capital}
            onChange={(e) => setCapital(e.target.value)}
          />
          {error && <p className="text-sm text-loss">{error}</p>}
          <Button type="submit" disabled={creating}>
            {creating ? "Creating…" : "Create portfolio"}
          </Button>
        </form>
      </Card>
    </div>
  );
}

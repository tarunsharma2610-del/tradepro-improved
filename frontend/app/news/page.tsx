"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { Card } from "@/components/ui/card";
import { api, ApiError } from "@/lib/api";

type InstrumentBrief = { id: string; trading_symbol: string; exchange: string };
type NewsItem = {
  id: string;
  title: string;
  link: string;
  summary: string | null;
  published_at: string | null;
  instruments: InstrumentBrief[];
};

export default function NewsPage() {
  const [items, setItems] = useState<NewsItem[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api
      .get<NewsItem[]>("/news")
      .then(setItems)
      .catch((err) => setError(err instanceof ApiError ? err.message : "Could not load news."))
      .finally(() => setLoading(false));
  }, []);

  return (
    <div className="mx-auto max-w-2xl p-8">
      <Link href="/" className="text-sm text-accent hover:underline">
        ← Dashboard
      </Link>
      <h1 className="mt-2 text-2xl font-semibold">Market news</h1>
      <p className="mt-1 text-sm text-ink/60 dark:text-paper/60">
        Tagged automatically against instruments you can trade here, by ticker and company name.
      </p>

      {loading && <p className="mt-6 text-sm text-ink/50 dark:text-paper/50">Loading…</p>}
      {error && <p className="mt-6 text-sm text-loss">{error}</p>}
      {!loading && !error && items.length === 0 && (
        <p className="mt-6 text-sm text-ink/50 dark:text-paper/50">
          No news ingested yet. An admin needs to add a source and run ingestion (Settings → Platform, or it runs
          automatically every 30 minutes once a source exists).
        </p>
      )}

      <div className="mt-6 space-y-3">
        {items.map((item) => (
          <Card key={item.id}>
            <a href={item.link} target="_blank" rel="noreferrer" className="font-medium hover:text-accent">
              {item.title}
            </a>
            {item.summary && <p className="mt-1 text-sm text-ink/60 dark:text-paper/60">{item.summary}</p>}
            <div className="mt-2 flex flex-wrap items-center gap-2">
              {item.published_at && (
                <span className="text-xs text-ink/40 dark:text-paper/40">
                  {new Date(item.published_at).toLocaleString("en-IN")}
                </span>
              )}
              {item.instruments.map((i) => (
                <span key={i.id} className="rounded-full bg-accent/10 px-2 py-0.5 text-xs font-medium text-accent">
                  {i.trading_symbol}
                </span>
              ))}
            </div>
          </Card>
        ))}
      </div>
    </div>
  );
}

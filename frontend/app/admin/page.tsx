"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { api, ApiError } from "@/lib/api";

type Stats = {
  total_users: number;
  total_portfolios: number;
  total_active_strategies: number;
  total_strategies: number;
  total_news_items: number;
  total_backtest_runs: number;
};
type PlatformSetting = { key: string; value_masked: string; description: string | null; updated_at: string };
type NewsSource = { id: string; name: string; rss_url: string; is_active: boolean; last_fetched_at: string | null; last_error: string | null };

const SETTING_KEYS = [
  { key: "ai_provider_api_key", label: "AI provider API key (Anthropic)" },
  { key: "telegram_bot_token", label: "Telegram bot token" },
  { key: "whatsapp_api_token", label: "WhatsApp Cloud API token" },
  { key: "whatsapp_phone_number_id", label: "WhatsApp phone number ID" },
  { key: "news_api_key", label: "News API key (reserved, not yet used)" },
];

export default function AdminPage() {
  const [stats, setStats] = useState<Stats | null>(null);
  const [settingsList, setSettingsList] = useState<PlatformSetting[]>([]);
  const [sources, setSources] = useState<NewsSource[]>([]);
  const [settingKey, setSettingKey] = useState(SETTING_KEYS[0].key);
  const [settingValue, setSettingValue] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [notice, setNotice] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    refresh();
  }, []);

  async function refresh() {
    try {
      const [s, settingsData, sourcesData] = await Promise.all([
        api.get<Stats>("/admin/stats"),
        api.get<PlatformSetting[]>("/settings/platform"),
        api.get<NewsSource[]>("/news/sources"),
      ]);
      setStats(s);
      setSettingsList(settingsData);
      setSources(sourcesData);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Could not load admin data — are you an admin?");
    }
  }

  async function onSaveSetting(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    setNotice(null);
    setBusy(true);
    try {
      await api.put("/settings/platform", { key: settingKey, value: settingValue });
      setSettingValue("");
      setNotice(`Saved ${settingKey}.`);
      await refresh();
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Could not save setting.");
    } finally {
      setBusy(false);
    }
  }

  async function onSeedAndIngestNews() {
    setBusy(true);
    setError(null);
    try {
      await api.post("/news/seed-default-source");
      const result = await api.post<{ ingested_per_source: Record<string, number> }>("/news/ingest");
      setNotice(`Ingested: ${JSON.stringify(result.ingested_per_source)}`);
      await refresh();
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Could not ingest news.");
    } finally {
      setBusy(false);
    }
  }

  async function onSeedInstruments() {
    setBusy(true);
    setError(null);
    try {
      const result = await api.post<{ seeded: number }>("/instruments/seed");
      setNotice(`Seeded ${result.seeded} instruments.`);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Could not seed instruments.");
    } finally {
      setBusy(false);
    }
  }

  if (error && !stats) {
    return (
      <div className="mx-auto max-w-2xl p-8">
        <p className="text-sm text-loss">{error}</p>
      </div>
    );
  }

  return (
    <div className="mx-auto max-w-2xl p-8">
      <Link href="/" className="text-sm text-accent hover:underline">
        ← Dashboard
      </Link>
      <h1 className="mt-2 text-2xl font-semibold">Admin</h1>

      {stats && (
        <div className="mt-6 grid grid-cols-3 gap-3">
          <Card><p className="text-xs text-ink/50 dark:text-paper/50">Users</p><p className="tabular text-xl">{stats.total_users}</p></Card>
          <Card><p className="text-xs text-ink/50 dark:text-paper/50">Portfolios</p><p className="tabular text-xl">{stats.total_portfolios}</p></Card>
          <Card><p className="text-xs text-ink/50 dark:text-paper/50">Active strategies</p><p className="tabular text-xl">{stats.total_active_strategies}<span className="text-sm text-ink/40 dark:text-paper/40">/{stats.total_strategies}</span></p></Card>
          <Card><p className="text-xs text-ink/50 dark:text-paper/50">News items</p><p className="tabular text-xl">{stats.total_news_items}</p></Card>
          <Card><p className="text-xs text-ink/50 dark:text-paper/50">Backtests run</p><p className="tabular text-xl">{stats.total_backtest_runs}</p></Card>
        </div>
      )}

      <Card className="mt-6">
        <h2 className="font-medium">Platform integration keys</h2>
        <p className="mt-1 text-xs text-ink/50 dark:text-paper/50">Shared platform-wide, encrypted at rest, never shown in full once saved.</p>
        <div className="mt-3 space-y-1 text-sm">
          {settingsList.map((s) => (
            <div key={s.key} className="flex justify-between border-b border-ink/5 py-1 dark:border-paper/5">
              <span className="text-ink/60 dark:text-paper/60">{s.key}</span>
              <span className="tabular">{s.value_masked}</span>
            </div>
          ))}
          {settingsList.length === 0 && <p className="text-ink/40 dark:text-paper/40">Nothing configured yet.</p>}
        </div>

        <form onSubmit={onSaveSetting} className="mt-4 space-y-3">
          <div className="flex flex-col gap-1.5">
            <label className="text-sm font-medium text-ink/80 dark:text-paper/80">Setting</label>
            <select value={settingKey} onChange={(e) => setSettingKey(e.target.value)} className="rounded-md border border-ink/15 bg-white px-3 py-2 text-sm dark:border-paper/20 dark:bg-ink-soft">
              {SETTING_KEYS.map((s) => (
                <option key={s.key} value={s.key}>{s.label}</option>
              ))}
            </select>
          </div>
          <Input label="Value" type="password" required value={settingValue} onChange={(e) => setSettingValue(e.target.value)} />
          <Button type="submit" disabled={busy || !settingValue}>{busy ? "Saving…" : "Save"}</Button>
        </form>
      </Card>

      <Card className="mt-6">
        <h2 className="font-medium">News sources</h2>
        <div className="mt-3 space-y-2 text-sm">
          {sources.map((s) => (
            <div key={s.id} className="border-b border-ink/5 pb-2 dark:border-paper/5">
              <p className="font-medium">{s.name}</p>
              <p className="text-xs text-ink/50 dark:text-paper/50">{s.rss_url}</p>
              {s.last_error && <p className="text-xs text-loss">{s.last_error}</p>}
              {s.last_fetched_at && !s.last_error && <p className="text-xs text-gain">Last fetched {new Date(s.last_fetched_at).toLocaleString("en-IN")}</p>}
            </div>
          ))}
          {sources.length === 0 && <p className="text-ink/40 dark:text-paper/40">No sources yet.</p>}
        </div>
        <Button variant="ghost" className="mt-3" onClick={onSeedAndIngestNews} disabled={busy}>
          {busy ? "Working…" : "Seed default source + ingest now"}
        </Button>
      </Card>

      <Card className="mt-6">
        <h2 className="font-medium">Instruments</h2>
        <p className="mt-1 text-xs text-ink/50 dark:text-paper/50">Seeds 10 real NSE large-caps. Needed before anyone can trade.</p>
        <Button variant="ghost" className="mt-3" onClick={onSeedInstruments} disabled={busy}>
          {busy ? "Seeding…" : "Seed default instruments"}
        </Button>
      </Card>

      {error && <p className="mt-4 text-sm text-loss">{error}</p>}
      {notice && <p className="mt-4 text-sm text-gain">{notice}</p>}
    </div>
  );
}

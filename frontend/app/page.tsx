"use client";

import { useEffect, useState } from "react";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { api, ApiError } from "@/lib/api";

type Connection = {
  id: string;
  broker: string;
  api_key_masked: string;
  is_connected: boolean;
  last_connected_at: string | null;
  last_error: string | null;
};

export default function BrokerSettingsPage() {
  const [connections, setConnections] = useState<Connection[]>([]);
  const [apiKey, setApiKey] = useState("");
  const [apiSecret, setApiSecret] = useState("");
  const [redirectUri, setRedirectUri] = useState("");
  const [saving, setSaving] = useState(false);
  const [busyBroker, setBusyBroker] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [notice, setNotice] = useState<string | null>(null);

  useEffect(() => {
    if (typeof window !== "undefined") {
      setRedirectUri(`${window.location.origin}/settings/broker/callback`);
    }
    refresh();
  }, []);

  async function refresh() {
    try {
      const list = await api.get<Connection[]>("/settings/broker");
      setConnections(list);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Could not load broker connections.");
    }
  }

  async function onSave(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    setNotice(null);
    setSaving(true);
    try {
      await api.put("/settings/broker", { broker: "upstox", api_key: apiKey, api_secret: apiSecret, redirect_uri: redirectUri });
      setApiKey("");
      setApiSecret("");
      setNotice("Saved. Click \u201cConnect via Upstox\u201d below to finish linking your account.");
      await refresh();
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Could not save credentials.");
    } finally {
      setSaving(false);
    }
  }

  async function onConnect(broker: string) {
    setBusyBroker(broker);
    setError(null);
    try {
      const { authorize_url } = await api.get<{ authorize_url: string }>(`/settings/broker/${broker}/authorize-url`);
      window.location.href = authorize_url;
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Could not start the broker login.");
      setBusyBroker(null);
    }
  }

  async function onTest(broker: string) {
    setBusyBroker(broker);
    setError(null);
    setNotice(null);
    try {
      const result = await api.post<{ success: boolean; message: string }>(`/settings/broker/${broker}/test`);
      setNotice(result.message);
      await refresh();
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Connection test failed.");
    } finally {
      setBusyBroker(null);
    }
  }

  async function onRemove(broker: string) {
    setBusyBroker(broker);
    setError(null);
    try {
      await api.del(`/settings/broker/${broker}`);
      await refresh();
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Could not remove connection.");
    } finally {
      setBusyBroker(null);
    }
  }

  return (
    <div className="mx-auto max-w-2xl p-8">
      <h1 className="text-2xl font-semibold">Broker connections</h1>
      <p className="mt-1 text-sm text-ink/60 dark:text-paper/60">
        Your Upstox API key and secret are encrypted before they touch the database and are never sent back to the
        browser in full. This replaces putting broker keys in a <code className="tabular">.env</code> file.
      </p>

      {connections.length > 0 && (
        <div className="mt-6 space-y-3">
          {connections.map((c) => (
            <Card key={c.id} className="flex items-center justify-between">
              <div>
                <div className="flex items-center gap-2">
                  <span className="font-medium capitalize">{c.broker}</span>
                  <span
                    className={`rounded-full px-2 py-0.5 text-xs font-medium ${
                      c.is_connected ? "bg-gain/15 text-gain" : "bg-caution/15 text-caution"
                    }`}
                  >
                    {c.is_connected ? "Connected" : "Not connected"}
                  </span>
                </div>
                <p className="tabular mt-1 text-sm text-ink/50 dark:text-paper/50">{c.api_key_masked}</p>
                {c.last_error && <p className="mt-1 text-sm text-loss">{c.last_error}</p>}
              </div>
              <div className="flex gap-2">
                {!c.is_connected && (
                  <Button variant="ghost" disabled={busyBroker === c.broker} onClick={() => onConnect(c.broker)}>
                    Connect via Upstox
                  </Button>
                )}
                {c.is_connected && (
                  <Button variant="ghost" disabled={busyBroker === c.broker} onClick={() => onTest(c.broker)}>
                    Test
                  </Button>
                )}
                <Button variant="ghost" disabled={busyBroker === c.broker} onClick={() => onRemove(c.broker)}>
                  Remove
                </Button>
              </div>
            </Card>
          ))}
        </div>
      )}

      <Card className="mt-6">
        <form onSubmit={onSave} className="space-y-4">
          <h2 className="font-medium">Add or update Upstox credentials</h2>
          <Input label="API key" required value={apiKey} onChange={(e) => setApiKey(e.target.value)} />
          <Input
            label="API secret"
            type="password"
            required
            value={apiSecret}
            onChange={(e) => setApiSecret(e.target.value)}
          />
          <Input
            label="Redirect URI"
            required
            value={redirectUri}
            onChange={(e) => setRedirectUri(e.target.value)}
          />
          <p className="-mt-2 text-xs text-ink/50 dark:text-paper/50">
            Register this exact URL as the redirect URI in your Upstox developer app.
          </p>

          {error && <p className="text-sm text-loss">{error}</p>}
          {notice && <p className="text-sm text-gain">{notice}</p>}

          <Button type="submit" disabled={saving}>
            {saving ? "Saving…" : "Save credentials"}
          </Button>
        </form>
      </Card>
    </div>
  );
}

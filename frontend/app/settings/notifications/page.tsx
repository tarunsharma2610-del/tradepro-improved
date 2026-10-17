"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { api, ApiError } from "@/lib/api";

type TelegramStatus = { linked: boolean; linked_at: string | null };

export default function NotificationSettingsPage() {
  const [telegramStatus, setTelegramStatus] = useState<TelegramStatus | null>(null);
  const [deepLink, setDeepLink] = useState<string | null>(null);
  const [whatsappNumber, setWhatsappNumber] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [notice, setNotice] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    refresh();
  }, []);

  async function refresh() {
    try {
      const [status, wa] = await Promise.all([
        api.get<TelegramStatus>("/settings/telegram/status"),
        api.get<{ whatsapp_number: string | null }>("/settings/whatsapp"),
      ]);
      setTelegramStatus(status);
      setWhatsappNumber(wa.whatsapp_number || "");
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Could not load notification settings.");
    }
  }

  async function onStartTelegramLink() {
    setError(null);
    setBusy(true);
    try {
      const result = await api.post<{ telegram_deep_link: string }>("/settings/telegram/link");
      setDeepLink(result.telegram_deep_link);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Could not start linking.");
    } finally {
      setBusy(false);
    }
  }

  async function onUnlinkTelegram() {
    setBusy(true);
    try {
      await api.del("/settings/telegram/link");
      setDeepLink(null);
      await refresh();
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Could not unlink.");
    } finally {
      setBusy(false);
    }
  }

  async function onSaveWhatsapp(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    setNotice(null);
    setBusy(true);
    try {
      await api.put("/settings/whatsapp", { whatsapp_number: whatsappNumber || null });
      setNotice("Saved.");
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Could not save.");
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="mx-auto max-w-2xl p-8">
      <Link href="/" className="text-sm text-accent hover:underline">
        ← Dashboard
      </Link>
      <h1 className="mt-2 text-2xl font-semibold">Notifications</h1>
      <p className="mt-1 text-sm text-ink/60 dark:text-paper/60">
        Get a message when a strategy enters or exits a trade.
      </p>

      <Card className="mt-6">
        <h2 className="font-medium">Telegram</h2>
        {telegramStatus?.linked ? (
          <div className="mt-3">
            <p className="text-sm text-gain">Linked{telegramStatus.linked_at ? ` since ${new Date(telegramStatus.linked_at).toLocaleDateString("en-IN")}` : ""}.</p>
            <Button variant="ghost" className="mt-3" onClick={onUnlinkTelegram} disabled={busy}>
              Unlink
            </Button>
          </div>
        ) : (
          <div className="mt-3">
            {!deepLink ? (
              <Button onClick={onStartTelegramLink} disabled={busy}>
                {busy ? "Starting…" : "Link Telegram"}
              </Button>
            ) : (
              <div className="space-y-2">
                <a
                  href={deepLink}
                  target="_blank"
                  rel="noreferrer"
                  className="inline-block rounded-md bg-accent px-4 py-2 text-sm text-white hover:bg-accent-soft"
                >
                  Open Telegram to finish linking →
                </a>
                <p className="text-xs text-ink/50 dark:text-paper/50">
                  Tap Start in the chat that opens. This page checks again automatically — refresh in a minute if it
                  doesn't update on its own.
                </p>
              </div>
            )}
          </div>
        )}
      </Card>

      <Card className="mt-6">
        <form onSubmit={onSaveWhatsapp} className="space-y-3">
          <h2 className="font-medium">WhatsApp</h2>
          <Input
            label="Phone number (E.164 format)"
            placeholder="+919876543210"
            value={whatsappNumber}
            onChange={(e) => setWhatsappNumber(e.target.value)}
          />
          <p className="text-xs text-ink/50 dark:text-paper/50">
            WhatsApp only delivers a message like this within 24 hours of you last messaging the platform's business
            number — that's a WhatsApp platform rule, not something this app controls.
          </p>
          <Button type="submit" disabled={busy}>
            {busy ? "Saving…" : "Save"}
          </Button>
        </form>
      </Card>

      {error && <p className="mt-4 text-sm text-loss">{error}</p>}
      {notice && <p className="mt-4 text-sm text-gain">{notice}</p>}
    </div>
  );
}

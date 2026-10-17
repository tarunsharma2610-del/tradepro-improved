"use client";

import Link from "next/link";
import { useSearchParams } from "next/navigation";
import { Suspense, useEffect, useState } from "react";
import { api, ApiError } from "@/lib/api";

type Status = "working" | "success" | "error";

function CallbackHandler() {
  const params = useSearchParams();
  const [status, setStatus] = useState<Status>("working");
  const [message, setMessage] = useState("Finishing your Upstox connection…");

  useEffect(() => {
    const code = params.get("code");
    const state = params.get("state");
    const broker = "upstox"; // Phase 1 supports one broker; the code param alone doesn't say which.

    if (!code || !state) {
      setStatus("error");
      setMessage("Upstox did not return the required authorization code and state. Restart the connection flow.");
      return;
    }

    api
      .post<{ is_connected: boolean; last_error: string | null }>(`/settings/broker/${broker}/callback`, { code, state })
      .then((result) => {
        if (result.is_connected) {
          setStatus("success");
          setMessage("Your Upstox account is connected.");
        } else {
          setStatus("error");
          setMessage(result.last_error || "Upstox accepted the login, but the connection could not be verified.");
        }
      })
      .catch((err) => {
        setStatus("error");
        setMessage(err instanceof ApiError ? err.message : "Something went wrong completing the connection.");
      });
  }, [params]);

  return (
    <div className="max-w-sm text-center">
      <p className={status === "error" ? "text-loss" : status === "success" ? "text-gain" : "text-ink/70 dark:text-paper/70"}>
        {message}
      </p>
      <Link href="/settings/broker" className="mt-4 inline-block text-sm text-accent hover:underline">
        Back to broker settings
      </Link>
    </div>
  );
}

export default function BrokerCallbackPage() {
  return (
    <div className="flex min-h-screen items-center justify-center p-8">
      <Suspense fallback={<p className="text-ink/70 dark:text-paper/70">Loading…</p>}>
        <CallbackHandler />
      </Suspense>
    </div>
  );
}

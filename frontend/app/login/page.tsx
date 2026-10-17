"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { api, ApiError } from "@/lib/api";

const TICKER = [
  { sym: "NIFTY 50", px: "24,812.35", chg: "+0.42%", up: true },
  { sym: "SENSEX", px: "81,203.10", chg: "+0.38%", up: true },
  { sym: "RELIANCE", px: "2,948.60", chg: "-0.15%", up: false },
  { sym: "HDFCBANK", px: "1,742.05", chg: "+0.61%", up: true },
  { sym: "TCS", px: "4,103.90", chg: "-0.22%", up: false },
];

export default function LoginPage() {
  const router = useRouter();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [mfaCode, setMfaCode] = useState("");
  const [mfaRequired, setMfaRequired] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    setLoading(true);
    try {
      const result = await api.post<{ mfa_required?: boolean; id?: string }>("/auth/login", {
        email,
        password,
        mfa_code: mfaCode || undefined,
      });
      if (result.mfa_required) {
        setMfaRequired(true);
      } else {
        router.push("/");
      }
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Something went wrong. Try again.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="grid min-h-screen grid-cols-1 md:grid-cols-2">
      {/* Signature panel — a quiet market-data motif, grounds the page in what this product actually does */}
      <div className="hidden md:flex flex-col justify-between bg-ink p-10 text-paper">
        <div className="text-lg font-semibold tracking-tight">Trading Platform</div>
        <div>
          <p className="mb-4 text-sm uppercase tracking-widest text-paper/50">Paper mode · live market data</p>
          <div className="space-y-1 tabular text-sm">
            {TICKER.map((row) => (
              <div key={row.sym} className="flex items-center justify-between border-b border-paper/10 py-2">
                <span className="text-paper/70">{row.sym}</span>
                <span className="text-paper">{row.px}</span>
                <span className={row.up ? "text-gain" : "text-loss"}>{row.chg}</span>
              </div>
            ))}
          </div>
          <p className="mt-4 text-xs text-paper/40">Illustrative layout only — not live data.</p>
        </div>
        <p className="text-xs text-paper/40">NSE · BSE · MCX</p>
      </div>

      {/* Form panel */}
      <div className="flex items-center justify-center p-8">
        <form onSubmit={onSubmit} className="w-full max-w-sm space-y-5">
          <div>
            <h1 className="text-2xl font-semibold">Log in</h1>
            <p className="mt-1 text-sm text-ink/60 dark:text-paper/60">
              New here?{" "}
              <Link href="/register" className="text-accent hover:underline">
                Create an account
              </Link>
            </p>
          </div>

          <Input label="Email" type="email" required value={email} onChange={(e) => setEmail(e.target.value)} />
          <Input
            label="Password"
            type="password"
            required
            value={password}
            onChange={(e) => setPassword(e.target.value)}
          />

          {mfaRequired && (
            <Input
              label="6-digit authenticator code"
              inputMode="numeric"
              maxLength={6}
              required
              value={mfaCode}
              onChange={(e) => setMfaCode(e.target.value)}
            />
          )}

          {error && <p className="text-sm text-loss">{error}</p>}

          <Button type="submit" disabled={loading} className="w-full">
            {loading ? "Logging in…" : "Log in"}
          </Button>
        </form>
      </div>
    </div>
  );
}

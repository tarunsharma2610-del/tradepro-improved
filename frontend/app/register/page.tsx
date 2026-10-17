"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { api, ApiError } from "@/lib/api";

export default function RegisterPage() {
  const router = useRouter();
  const [fullName, setFullName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    setLoading(true);
    try {
      await api.post("/auth/register", { email, password, full_name: fullName });
      await api.post("/auth/login", { email, password });
      router.push("/");
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Something went wrong. Try again.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="flex min-h-screen items-center justify-center bg-paper-soft p-8 dark:bg-ink">
      <Card className="w-full max-w-sm">
        <form onSubmit={onSubmit} className="space-y-5">
          <div>
            <h1 className="text-2xl font-semibold">Create your account</h1>
            <p className="mt-1 text-sm text-ink/60 dark:text-paper/60">
              Already have one?{" "}
              <Link href="/login" className="text-accent hover:underline">
                Log in
              </Link>
            </p>
          </div>

          <Input label="Full name" required value={fullName} onChange={(e) => setFullName(e.target.value)} />
          <Input label="Email" type="email" required value={email} onChange={(e) => setEmail(e.target.value)} />
          <Input
            label="Password"
            type="password"
            required
            minLength={10}
            value={password}
            onChange={(e) => setPassword(e.target.value)}
          />
          <p className="-mt-3 text-xs text-ink/50 dark:text-paper/50">At least 10 characters.</p>

          {error && <p className="text-sm text-loss">{error}</p>}

          <Button type="submit" disabled={loading} className="w-full">
            {loading ? "Creating account…" : "Create account"}
          </Button>
        </form>
      </Card>
    </div>
  );
}

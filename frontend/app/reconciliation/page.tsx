"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { ApiError, api } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";

type Run = {
  id: string;
  broker_connection_id: string;
  status: "RUNNING" | "COMPLETED" | "COMPLETED_WITH_CONFLICTS" | "FAILED" | "LEASE_LOST";
  started_at: string;
  completed_at: string | null;
  error_code: string | null;
  summary: Record<string, number> | null;
};

type Issue = {
  id: string;
  broker_connection_id: string;
  run_id: string | null;
  intent_id: string | null;
  issue_type: string;
  broker_order_id: string | null;
  broker_trade_id: string | null;
  status: "OPEN" | "RESOLVED";
  safe_details: Record<string, string | number | boolean | null> | null;
  first_seen_at: string;
  last_seen_at: string;
  occurrence_count: number;
  resolved_at: string | null;
};

function dateTime(value: string | null) {
  if (!value) return "—";
  const parsed = new Date(value);
  return Number.isNaN(parsed.getTime()) ? "—" : parsed.toLocaleString("en-IN");
}

function statusClass(status: string) {
  if (status === "COMPLETED") return "text-profit";
  if (status === "COMPLETED_WITH_CONFLICTS" || status === "FAILED" || status === "LEASE_LOST") return "text-loss";
  return "text-ink/60 dark:text-paper/60";
}

export default function ReconciliationPage() {
  const [runs, setRuns] = useState<Run[]>([]);
  const [issues, setIssues] = useState<Issue[]>([]);
  const [issueStatus, setIssueStatus] = useState<"OPEN" | "RESOLVED" | "ALL">("OPEN");
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [needsLogin, setNeedsLogin] = useState(false);

  async function refresh(showSpinner = true) {
    if (showSpinner) setRefreshing(true);
    setError(null);
    try {
      const issueQuery = issueStatus === "ALL" ? "" : `?status=${issueStatus}`;
      const [runRows, issueRows] = await Promise.all([
        api.get<Run[]>("/reconciliation/runs?limit=100"),
        api.get<Issue[]>(`/reconciliation/issues?limit=100${issueQuery ? `&${issueQuery.slice(1)}` : ""}`),
      ]);
      setRuns(runRows);
      setIssues(issueRows);
      setNeedsLogin(false);
    } catch (err) {
      if (err instanceof ApiError && err.status === 401) {
        setNeedsLogin(true);
        setError("Please log in to review reconciliation records.");
      } else {
        setError(err instanceof ApiError ? err.message : "Could not load reconciliation records.");
      }
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }

  useEffect(() => {
    void refresh(false);
    // Load on entry; manual refresh and status selection trigger subsequent reads.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  useEffect(() => {
    if (!loading) void refresh(false);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [issueStatus]);

  return (
    <main className="mx-auto max-w-6xl space-y-6 p-6 sm:p-8">
      <header className="flex flex-col gap-3 sm:flex-row sm:items-end sm:justify-between">
        <div>
          <Link href="/" className="text-sm text-accent hover:underline">← Dashboard</Link>
          <h1 className="mt-2 text-3xl font-semibold">Reconciliation review</h1>
          <p className="mt-2 max-w-3xl text-sm text-ink/60 dark:text-paper/60">
            Review read-only reconciliation summaries and items that need manual investigation. This page does not start a broker poll, place orders, or resolve issues.
          </p>
        </div>
        <Button variant="ghost" onClick={() => void refresh()} disabled={refreshing}>
          {refreshing ? "Refreshing…" : "Refresh"}
        </Button>
      </header>

      {error && (
        <Card className="border-loss/30">
          <p className="text-sm text-loss">{error}</p>
          {needsLogin && <div className="mt-3"><Link href="/login"><Button>Go to login</Button></Link></div>}
        </Card>
      )}

      <section className="space-y-3">
        <div>
          <h2 className="text-xl font-semibold">Recent runs</h2>
          <p className="text-sm text-ink/60 dark:text-paper/60">Latest 100 runs. A RUNNING row may indicate a pass that has not completed or needs stale-run recovery.</p>
        </div>
        {loading ? <Card><p className="text-sm">Loading runs…</p></Card> : runs.length === 0 ? (
          <Card><p className="text-sm text-ink/60 dark:text-paper/60">No reconciliation runs recorded yet.</p></Card>
        ) : (
          <div className="space-y-3">
            {runs.map((run) => (
              <Card key={run.id} className="space-y-3">
                <div className="flex flex-wrap items-start justify-between gap-2">
                  <div>
                    <p className="font-medium">{run.status.replaceAll("_", " ")}</p>
                    <p className="mt-1 text-xs text-ink/50 dark:text-paper/50">Run {run.id.slice(0, 8)} · Connection {run.broker_connection_id.slice(0, 8)}</p>
                  </div>
                  <span className={`text-sm font-medium ${statusClass(run.status)}`}>{run.error_code ?? "No error"}</span>
                </div>
                <div className="grid gap-2 text-sm sm:grid-cols-2">
                  <p><span className="text-ink/50 dark:text-paper/50">Started:</span> {dateTime(run.started_at)}</p>
                  <p><span className="text-ink/50 dark:text-paper/50">Completed:</span> {dateTime(run.completed_at)}</p>
                </div>
                {run.error_code === "WORKER_INTERRUPTED" && (
                  <p role="alert" className="text-sm text-loss">
                    This run was interrupted before its summary could be finalized. The counters below may be incomplete; zero values do not prove that no fills were processed.
                  </p>
                )}
                {run.summary && (
                  <div className="grid grid-cols-2 gap-2 sm:grid-cols-4 lg:grid-cols-7">
                    {Object.entries(run.summary).map(([key, value]) => (
                      <div key={key} className="rounded-md bg-black/5 p-2 dark:bg-white/5">
                        <p className="text-xs text-ink/50 dark:text-paper/50">{key.replaceAll("_", " ")}</p>
                        <p className="mt-1 text-lg font-semibold tabular">{value}</p>
                      </div>
                    ))}
                  </div>
                )}
              </Card>
            ))}
          </div>
        )}
      </section>

      <section className="space-y-3">
        <div className="flex flex-col gap-2 sm:flex-row sm:items-end sm:justify-between">
          <div>
            <h2 className="text-xl font-semibold">Manual-review issues</h2>
            <p className="text-sm text-ink/60 dark:text-paper/60">Issue details are sanitized. Resolution controls are intentionally not available yet.</p>
          </div>
          <label className="flex items-center gap-2 text-sm">
            <span>Show</span>
            <select
              className="rounded-md border border-ink/20 bg-transparent px-3 py-2 dark:border-paper/20"
              value={issueStatus}
              onChange={(event) => setIssueStatus(event.target.value as "OPEN" | "RESOLVED" | "ALL")}
            >
              <option value="OPEN">Open only</option>
              <option value="RESOLVED">Resolved only</option>
              <option value="ALL">All issues</option>
            </select>
          </label>
        </div>
        {loading ? <Card><p className="text-sm">Loading issues…</p></Card> : issues.length === 0 ? (
          <Card><p className="text-sm text-ink/60 dark:text-paper/60">No issues match this filter.</p></Card>
        ) : (
          <div className="space-y-3">
            {issues.map((issue) => (
              <Card key={issue.id} className="space-y-2">
                <div className="flex flex-wrap items-start justify-between gap-2">
                  <div>
                    <p className="font-medium">{issue.issue_type.replaceAll("_", " ")}</p>
                    <p className="mt-1 text-xs text-ink/50 dark:text-paper/50">Issue {issue.id.slice(0, 8)} · Connection {issue.broker_connection_id.slice(0, 8)}</p>
                  </div>
                  <span className={issue.status === "OPEN" ? "text-loss text-sm font-medium" : "text-profit text-sm font-medium"}>{issue.status}</span>
                </div>
                <div className="grid gap-2 text-sm sm:grid-cols-2">
                  {issue.broker_order_id && <p><span className="text-ink/50 dark:text-paper/50">Broker order:</span> {issue.broker_order_id}</p>}
                  {issue.broker_trade_id && <p><span className="text-ink/50 dark:text-paper/50">Broker trade:</span> {issue.broker_trade_id}</p>}
                  <p><span className="text-ink/50 dark:text-paper/50">Occurrences:</span> {issue.occurrence_count}</p>
                  <p><span className="text-ink/50 dark:text-paper/50">Last seen:</span> {dateTime(issue.last_seen_at)}</p>
                </div>
                {issue.safe_details && (
                  <dl className="grid gap-1 rounded-md bg-black/5 p-3 text-sm dark:bg-white/5 sm:grid-cols-2">
                    {Object.entries(issue.safe_details).map(([key, value]) => (
                      <div key={key} className="flex gap-2">
                        <dt className="text-ink/50 dark:text-paper/50">{key.replaceAll("_", " ")}:</dt>
                        <dd className="break-all">{String(value ?? "—")}</dd>
                      </div>
                    ))}
                  </dl>
                )}
              </Card>
            ))}
          </div>
        )}
      </section>
    </main>
  );
}

import React, { useEffect, useMemo, useState } from "react";

// --- API base ---
const API = (p: string) => `http://localhost:8000${p}`;

// --- Types ---
export type Job = {
  id?: string;
  title: string;
  company: string;
  location?: string;
  source?: string; // greenhouse/lever/etc.
  url: string;
};

export type ApplicationItem = {
  id: number;
  url: string;
  company?: string;
  title?: string;
  portal?: string;
  status: "QUEUED"|"IN_PROGRESS"|"DRAFTED"|"SUBMITTED"|"DONE"|"FAILED"|string;
  attempts?: number;
  error?: string|null;
  created_at?: string;
  updated_at?: string;
  job?: any;
};

// --- API helpers (single-user) ---
async function fetchApplications(): Promise<ApplicationItem[]> {
  const res = await fetch(API("/applications"));
  if (!res.ok) throw new Error("Failed to fetch applications");
  return res.json();
}

export async function postApply(job: Job): Promise<{application_ids:number[]}> {
  const res = await fetch(API("/apply"), {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ jobs: [{ ...job, portal: job.source }] }),
  });
  if (!res.ok) throw new Error("Failed to enqueue application");
  return res.json();
}

// --- Hook: poll applications list and index by URL ---
export function useApplicationsPoll(intervalMs = 5000) {
  const [list, setList] = useState<ApplicationItem[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string|undefined>();

  useEffect(() => {
    let mounted = true;
    let timer: any;
    const run = async () => {
      try {
        setLoading(true);
        const data = await fetchApplications();
        if (mounted) setList(data);
      } catch (e:any) {
        if (mounted) setError(e?.message || "Error");
      } finally {
        if (mounted) setLoading(false);
      }
    };
    run();
    timer = setInterval(run, intervalMs);
    return () => {
      mounted = false;
      clearInterval(timer);
    };
  }, [intervalMs]);

  const byUrl = useMemo(() => {
    const m: Record<string, ApplicationItem> = {};
    for (const a of list) if (a.url) m[a.url] = a;
    return m;
  }, [list]);

  const runningCount = useMemo(() => list.filter(a => a.status === "QUEUED" || a.status === "IN_PROGRESS").length, [list]);

  return { list, byUrl, loading, error, runningCount };
}

// --- UI: status pill ---
export function StatusPill({ status }: { status: ApplicationItem["status"] }) {
  const label: Record<string,string> = {
    QUEUED: "Queued",
    IN_PROGRESS: "In progress",
    DRAFTED: "Drafted",
    SUBMITTED: "Submitted",
    DONE: "Done",
    FAILED: "Failed",
  };
  const base = "inline-flex items-center gap-2 rounded-full px-3 py-1 text-sm shadow-sm";
  const cls = {
    QUEUED: "bg-gray-100 text-gray-700",
    IN_PROGRESS: "bg-blue-100 text-blue-700",
    DRAFTED: "bg-amber-100 text-amber-700",
    SUBMITTED: "bg-indigo-100 text-indigo-700",
    DONE: "bg-green-100 text-green-700",
    FAILED: "bg-red-100 text-red-700",
  }[status] || "bg-gray-100 text-gray-700";
  return (
    <span className={`${base} ${cls}`}>
      <span className="h-2 w-2 rounded-full bg-current opacity-70"></span>
      {label[status] ?? status}
    </span>
  );
}

// --- UI: Apply button or status pill ---
export function ApplyOrStatusButton({ job, current }: { job: Job; current?: ApplicationItem }) {
  const [busy, setBusy] = useState(false);
  const canApply = !current;

  const onApply = async () => {
    try {
      setBusy(true);
      await postApply(job);
    } finally {
      setBusy(false);
    }
  };

  if (!canApply) return <StatusPill status={current.status} />;
  return (
    <button
      onClick={onApply}
      disabled={busy}
      className="rounded-xl bg-black px-4 py-2 text-white hover:opacity-90 disabled:opacity-60"
      title="Queue this job for auto-apply"
    >
      {busy ? "Queuing…" : "Apply"}
    </button>
  );
}

// --- Nav badge (top bar): show running count ---
export function ApplicationsNavBadge({ running }: { running: number }) {
  return (
    <div className="relative inline-flex items-center gap-2 rounded-xl bg-gray-100 px-3 py-1 text-sm text-gray-700">
      <span>Applications</span>
      <span className="rounded-md bg-white px-2 py-0.5 text-xs shadow">{running}</span>
      {running > 0 && <span className="ml-1 h-2 w-2 animate-pulse rounded-full bg-green-500" />}
    </div>
  );
}

// --- Applications panel (simple table) ---
export default function ApplicationsPanel() {
  const { list, loading } = useApplicationsPoll(4000);

  return (
    <div className="p-4">
      <div className="mb-3 flex items-center justify-between">
        <h2 className="text-xl font-semibold">Applications</h2>
        {loading && <span className="text-sm text-gray-500">Refreshing…</span>}
      </div>
      <div className="overflow-hidden rounded-2xl border">
        <table className="min-w-full text-sm">
          <thead className="bg-gray-50 text-left text-xs uppercase text-gray-500">
            <tr>
              <th className="px-4 py-3">Company</th>
              <th className="px-4 py-3">Title</th>
              <th className="px-4 py-3">Portal</th>
              <th className="px-4 py-3">Status</th>
              <th className="px-4 py-3">Updated</th>
              <th className="px-4 py-3">View</th>
            </tr>
          </thead>
          <tbody>
            {list.map((a) => (
              <tr key={a.id} className="border-t">
                <td className="px-4 py-3">{a.company || "—"}</td>
                <td className="px-4 py-3">{a.title || "—"}</td>
                <td className="px-4 py-3">{a.portal || "—"}</td>
                <td className="px-4 py-3"><StatusPill status={a.status} /></td>
                <td className="px-4 py-3">{a.updated_at ? new Date(a.updated_at).toLocaleString() : "—"}</td>
                <td className="px-4 py-3">
                  {a.job?.screenshot_url || a.job?.snapshot_url ? (
                    <div className="flex gap-2">
                      {a.job?.screenshot_url && (
                        <a className="underline" href={a.job.screenshot_url} target="_blank" rel="noreferrer">Screenshot</a>
                      )}
                      {a.job?.snapshot_url && (
                        <a className="underline" href={a.job.snapshot_url} target="_blank" rel="noreferrer">Snapshot</a>
                      )}
                    </div>
                  ) : (
                    <a className="underline opacity-60" href={a.url} target="_blank" rel="noreferrer">Job</a>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

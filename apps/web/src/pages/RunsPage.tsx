import { useEffect, useMemo, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { fetchProjectMetrics, fetchRuns } from "../api/client";
import type { ProjectMetrics, RunSummary } from "../api/types";
import { StatusBadge } from "../components/StatusBadge";

function fmtMs(value?: number | null): string {
  if (value == null) return "—";
  if (value >= 1000) return `${(value / 1000).toFixed(2)}s`;
  return `${Math.round(value)}ms`;
}

function fmtUsd(value?: number | null): string {
  if (value == null) return "—";
  return `$${Number(value).toFixed(6)}`;
}

export function RunsPage() {
  const { projectId = "" } = useParams();
  const [status, setStatus] = useState("");
  const [query, setQuery] = useState("");
  const [runs, setRuns] = useState<RunSummary[]>([]);
  const [metrics, setMetrics] = useState<ProjectMetrics | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    setError(null);
    Promise.all([
      fetchRuns(projectId, { status: status || undefined, limit: 100 }),
      fetchProjectMetrics(projectId),
    ])
      .then(([runData, metricData]) => {
        if (cancelled) return;
        setRuns(runData.items);
        setMetrics(metricData);
      })
      .catch((err: Error) => {
        if (!cancelled) setError(err.message);
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, [projectId, status]);

  const filtered = useMemo(() => {
    const q = query.trim().toLowerCase();
    if (!q) return runs;
    return runs.filter((run) =>
      [run.run_id, run.name, run.agent_name, run.agent_version, ...(run.tags ?? [])]
        .filter(Boolean)
        .some((v) => String(v).toLowerCase().includes(q)),
    );
  }, [runs, query]);

  return (
    <section>
      <div className="crumb">
        <Link to="/">Projects</Link>
        <span>/</span>
        <span className="mono">{projectId}</span>
      </div>
      <div className="page-head">
        <div>
          <h1>Runs</h1>
          <p className="muted">Filter and open a run to inspect its timeline.</p>
        </div>
      </div>

      {metrics && (
        <div className="grid-metrics">
          <div className="metric-tile">
            <div className="label">Runs</div>
            <div className="value">{metrics.run_count}</div>
          </div>
          <div className="metric-tile">
            <div className="label">Success rate</div>
            <div className="value">
              {metrics.success_rate == null
                ? "—"
                : `${(metrics.success_rate * 100).toFixed(0)}%`}
            </div>
          </div>
          <div className="metric-tile">
            <div className="label">p95 wall</div>
            <div className="value">{fmtMs(metrics.wall_ms.p95)}</div>
          </div>
          <div className="metric-tile">
            <div className="label">Total cost</div>
            <div className="value">{fmtUsd(metrics.total_estimated_cost_usd)}</div>
          </div>
        </div>
      )}

      <div className="panel panel-pad">
        <div className="toolbar">
          <select value={status} onChange={(e) => setStatus(e.target.value)}>
            <option value="">All statuses</option>
            <option value="succeeded">succeeded</option>
            <option value="failed">failed</option>
            <option value="running">running</option>
            <option value="cancelled">cancelled</option>
            <option value="timed_out">timed_out</option>
          </select>
          <input
            placeholder="Filter by id, name, tag…"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
          />
        </div>

        {loading && <div className="loading">Loading runs…</div>}
        {error && <div className="error-box">{error}</div>}
        {!loading && !error && filtered.length === 0 && (
          <div className="empty">No runs match this filter.</div>
        )}
        {!loading && !error && filtered.length > 0 && (
          <table className="table">
            <thead>
              <tr>
                <th>Run</th>
                <th>Status</th>
                <th>Wall</th>
                <th>Cost</th>
                <th>Retries</th>
                <th>Started</th>
              </tr>
            </thead>
            <tbody>
              {filtered.map((run) => (
                <tr key={run.run_id}>
                  <td>
                    <Link
                      className="row-link mono"
                      to={`/projects/${projectId}/runs/${run.run_id}`}
                    >
                      {run.run_id}
                    </Link>
                    <div className="muted">
                      {run.name || run.agent_name || "—"}
                      {run.agent_version ? ` · ${run.agent_version}` : ""}
                    </div>
                  </td>
                  <td>
                    <StatusBadge status={run.status} />
                  </td>
                  <td className="mono">{fmtMs(run.metrics_summary?.wall_ms)}</td>
                  <td className="mono">
                    {fmtUsd(run.metrics_summary?.estimated_cost_usd)}
                  </td>
                  <td className="mono">{run.metrics_summary?.retry_count ?? "—"}</td>
                  <td className="mono muted">
                    {run.started_at ? new Date(run.started_at).toLocaleString() : "—"}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </section>
  );
}

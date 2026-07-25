import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { fetchRun } from "../api/client";
import type { RunDetail } from "../api/types";
import { MetricsPanel } from "../components/MetricsPanel";
import { StatusBadge } from "../components/StatusBadge";
import { Waterfall } from "../components/Waterfall";

export function RunDetailPage() {
  const { projectId = "", runId = "" } = useParams();
  const [detail, setDetail] = useState<RunDetail | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    setError(null);
    fetchRun(projectId, runId)
      .then((data) => {
        if (!cancelled) setDetail(data);
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
  }, [projectId, runId]);

  return (
    <section>
      <div className="crumb">
        <Link to="/">Projects</Link>
        <span>/</span>
        <Link to={`/projects/${projectId}`}>{projectId}</Link>
        <span>/</span>
        <span className="mono">{runId}</span>
      </div>

      <div className="page-head">
        <div>
          <h1>Run detail</h1>
          <p className="muted">Timeline waterfall, derived metrics, and events.</p>
        </div>
        {detail?.run && <StatusBadge status={detail.run.status} />}
      </div>

      {loading && <div className="panel panel-pad loading">Loading run…</div>}
      {error && <div className="panel panel-pad error-box">{error}</div>}

      {detail && !loading && !error && (
        <div className="stack-2">
          <div className="panel panel-pad">
            <div className="split-2">
              <div>
                <h3 className="section-title">Summary</h3>
                <p className="mono">{detail.run.run_id}</p>
                <p className="muted">
                  {detail.run.name || detail.run.agent_name || "Untitled run"}
                  {detail.run.agent_version ? ` · ${detail.run.agent_version}` : ""}
                </p>
                <p className="mono muted">
                  {detail.run.started_at
                    ? new Date(detail.run.started_at).toLocaleString()
                    : "—"}
                  {" → "}
                  {detail.run.ended_at
                    ? new Date(detail.run.ended_at).toLocaleString()
                    : "—"}
                </p>
              </div>
              <div>
                <h3 className="section-title">Metrics</h3>
                <MetricsPanel metrics={detail.metrics} />
              </div>
            </div>
          </div>

          <div className="panel panel-pad">
            <h3 className="section-title">Timeline</h3>
            <Waterfall
              spans={detail.spans ?? []}
              runStart={detail.run.started_at}
              runEnd={detail.run.ended_at}
            />
          </div>

          <div className="panel panel-pad">
            <h3 className="section-title">Events</h3>
            {(detail.events ?? []).length === 0 ? (
              <div className="empty">No events recorded.</div>
            ) : (
              <ul className="event-list">
                {(detail.events ?? []).map((event) => (
                  <li key={event.event_id}>
                    <div>
                      <span className={`badge ${event.type}`}>{event.type}</span>{" "}
                      <span className="mono muted">{event.event_id}</span>
                    </div>
                    <div>{event.message || "—"}</div>
                    <div className="mono muted">
                      {event.timestamp
                        ? new Date(event.timestamp).toLocaleString()
                        : "—"}
                      {event.span_id ? ` · span ${event.span_id}` : ""}
                    </div>
                  </li>
                ))}
              </ul>
            )}
          </div>
        </div>
      )}
    </section>
  );
}

import type { RunMetrics } from "../api/types";

function fmtMs(value?: number | null): string {
  if (value == null || Number.isNaN(value)) return "—";
  if (value >= 1000) return `${(value / 1000).toFixed(2)}s`;
  return `${Math.round(value)}ms`;
}

function fmtUsd(value?: number | null): string {
  if (value == null || Number.isNaN(value)) return "—";
  if (value < 0.0001) return `$${value.toFixed(8)}`;
  return `$${value.toFixed(6)}`;
}

type Props = {
  metrics?: RunMetrics | null;
};

export function MetricsPanel({ metrics }: Props) {
  if (!metrics) {
    return <div className="empty">No metrics derived for this run yet.</div>;
  }

  const attribution = metrics.attribution_ms ?? {};
  const kinds = Object.keys(attribution).filter((k) => (attribution[k] ?? 0) > 0);
  const maxAttr = Math.max(...kinds.map((k) => attribution[k] ?? 0), 1);

  return (
    <div className="stack-2">
      <div className="grid-metrics">
        <div className="metric-tile">
          <div className="label">Wall time</div>
          <div className="value">{fmtMs(metrics.wall_ms)}</div>
        </div>
        <div className="metric-tile">
          <div className="label">Est. cost</div>
          <div className="value">{fmtUsd(metrics.estimated_cost_usd)}</div>
        </div>
        <div className="metric-tile">
          <div className="label">Tokens</div>
          <div className="value mono">
            {metrics.tokens?.in ?? 0}/{metrics.tokens?.out ?? 0}
          </div>
        </div>
        <div className="metric-tile">
          <div className="label">Retries</div>
          <div className="value">{metrics.retry_count ?? 0}</div>
        </div>
      </div>

      <div>
        <h3 className="section-title">Time by span kind</h3>
        {kinds.length === 0 ? (
          <div className="muted">No timed spans.</div>
        ) : (
          <div className="attr-bars">
            {kinds.map((kind) => {
              const ms = attribution[kind] ?? 0;
              const pct = (ms / maxAttr) * 100;
              return (
                <div className="attr-row" key={kind}>
                  <span className="mono">{kind}</span>
                  <div className="attr-fill">
                    <span style={{ width: `${pct}%` }} />
                  </div>
                  <span className="mono muted">{fmtMs(ms)}</span>
                </div>
              );
            })}
          </div>
        )}
      </div>
    </div>
  );
}

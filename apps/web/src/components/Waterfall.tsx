import type { Span } from "../api/types";

function parseTs(value?: string | null): number | null {
  if (!value) return null;
  const ms = Date.parse(value);
  return Number.isNaN(ms) ? null : ms;
}

function fmtMs(value: number): string {
  if (value >= 1000) return `${(value / 1000).toFixed(2)}s`;
  return `${Math.round(value)}ms`;
}

type Props = {
  spans: Span[];
  runStart?: string | null;
  runEnd?: string | null;
};

export function Waterfall({ spans, runStart, runEnd }: Props) {
  if (!spans.length) {
    return <div className="empty">No spans on this run.</div>;
  }

  const starts = spans.map((s) => parseTs(s.started_at)).filter((n): n is number => n != null);
  const ends = spans
    .map((s) => parseTs(s.ended_at) ?? parseTs(s.started_at))
    .filter((n): n is number => n != null);

  const origin =
    parseTs(runStart) ?? (starts.length ? Math.min(...starts) : Date.now());
  const horizon =
    parseTs(runEnd) ??
    (ends.length ? Math.max(...ends) : origin + 1);
  const total = Math.max(horizon - origin, 1);

  return (
    <div className="waterfall">
      {spans.map((span) => {
        const start = parseTs(span.started_at) ?? origin;
        const end = parseTs(span.ended_at) ?? start;
        const left = ((start - origin) / total) * 100;
        const width = Math.max(((end - start) / total) * 100, 0.4);
        const duration = Math.max(end - start, 0);
        return (
          <div className="waterfall-row" key={span.span_id}>
            <div className="waterfall-meta">
              <div className="name">{span.name}</div>
              <div className="sub">
                {span.kind} · {span.span_id}
              </div>
            </div>
            <div className="track" title={`${span.kind} ${span.status}`}>
              <div
                className={`bar ${span.kind}${span.status === "error" ? " error" : ""}`}
                style={{ left: `${left}%`, width: `${width}%` }}
              />
            </div>
            <div className="duration">{fmtMs(duration)}</div>
          </div>
        );
      })}
    </div>
  );
}

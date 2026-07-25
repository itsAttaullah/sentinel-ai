import { useEffect, useState } from "react";
import { Link, useParams, useSearchParams } from "react-router-dom";
import { fetchBenchmarkSuites, fetchLeaderboard } from "../api/client";
import type { BenchmarkSuite, LeaderboardReport } from "../api/types";

function fmtRate(value: number | null | undefined): string {
  if (value == null) return "—";
  return `${(value * 100).toFixed(0)}%`;
}

function fmtNum(value: number | null | undefined, digits = 3): string {
  if (value == null) return "—";
  return Number(value).toFixed(digits);
}

function fmtMs(value: number | null | undefined): string {
  if (value == null) return "—";
  if (value >= 1000) return `${(value / 1000).toFixed(2)}s`;
  return `${Math.round(value)}ms`;
}

export function BenchmarksPage() {
  const { projectId = "", benchmarkId } = useParams();
  const [searchParams, setSearchParams] = useSearchParams();
  const baseline = searchParams.get("baseline") ?? "";

  const [suites, setSuites] = useState<BenchmarkSuite[]>([]);
  const [report, setReport] = useState<LeaderboardReport | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    setError(null);
    fetchBenchmarkSuites(projectId)
      .then((data) => {
        if (!cancelled) setSuites(data.items);
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
  }, [projectId]);

  useEffect(() => {
    if (!benchmarkId) {
      setReport(null);
      return;
    }
    let cancelled = false;
    setLoading(true);
    setError(null);
    fetchLeaderboard(projectId, benchmarkId, {
      baseline_agent_version: baseline || undefined,
    })
      .then((data) => {
        if (!cancelled) setReport(data);
      })
      .catch((err: Error) => {
        if (!cancelled) {
          setReport(null);
          setError(err.message);
        }
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, [projectId, benchmarkId, baseline]);

  return (
    <section>
      <div className="crumb">
        <Link to="/">Projects</Link>
        <span>/</span>
        <Link to={`/projects/${encodeURIComponent(projectId)}`}>{projectId}</Link>
        <span>/</span>
        <span>Benchmarks</span>
      </div>
      <div className="page-head">
        <div>
          <h1>Benchmarks</h1>
          <p className="muted">
            Config matrix leaderboards. Sentinel compares recorded runs — it does not
            execute agents.
          </p>
        </div>
      </div>

      {error && <p className="error-banner">{error}</p>}
      {loading && !report && !suites.length && <p className="muted">Loading…</p>}

      <div className="panel">
        <h2>Suites</h2>
        {suites.length === 0 ? (
          <p className="muted">No benchmark suites registered for this project.</p>
        ) : (
          <ul className="suite-list">
            {suites.map((suite) => (
              <li key={`${suite.benchmark_id}@${suite.version}`}>
                <Link
                  to={`/projects/${encodeURIComponent(projectId)}/benchmarks/${encodeURIComponent(suite.benchmark_id)}`}
                >
                  <strong>{suite.name}</strong>
                  <span className="mono">
                    {suite.benchmark_id}@{suite.version}
                  </span>
                </Link>
              </li>
            ))}
          </ul>
        )}
      </div>

      {benchmarkId && (
        <div className="panel">
          <div className="page-head">
            <div>
              <h2>{report?.name ?? benchmarkId}</h2>
              <p className="muted mono">
                {report
                  ? `${report.benchmark_id}@${report.benchmark_version} · ${report.cell_count} cells · ${report.group_count} configs`
                  : benchmarkId}
              </p>
            </div>
            <label className="filter">
              Baseline agent version
              <input
                value={baseline}
                placeholder="e.g. 0.1.0"
                onChange={(event) => {
                  const value = event.target.value;
                  const next = new URLSearchParams(searchParams);
                  if (value) next.set("baseline", value);
                  else next.delete("baseline");
                  setSearchParams(next);
                }}
              />
            </label>
          </div>

          {report && (
            <>
              <div className="table-wrap">
                <table className="data-table">
                  <thead>
                    <tr>
                      <th>#</th>
                      <th>Config</th>
                      <th>Pass</th>
                      <th>Score</th>
                      <th>Wall</th>
                      <th>Cost</th>
                      <th>Cells</th>
                    </tr>
                  </thead>
                  <tbody>
                    {report.leaderboard.map((row) => (
                      <tr key={row.dimensions_key}>
                        <td>{row.rank}</td>
                        <td className="mono">{row.dimensions_key}</td>
                        <td>{fmtRate(row.pass_rate)}</td>
                        <td>{fmtNum(row.mean_score)}</td>
                        <td>{fmtMs(row.mean_wall_ms)}</td>
                        <td>{fmtNum(row.mean_cost_usd, 6)}</td>
                        <td>{row.cell_count}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>

              {report.pairwise.length > 0 && (
                <>
                  <h3>vs baseline {baseline}</h3>
                  <div className="table-wrap">
                    <table className="data-table">
                      <thead>
                        <tr>
                          <th>Candidate</th>
                          <th>Δ pass</th>
                          <th>Δ score</th>
                          <th>Δ wall</th>
                        </tr>
                      </thead>
                      <tbody>
                        {report.pairwise.map((row, index) => (
                          <tr key={index}>
                            <td className="mono">
                              {Object.entries(row.candidate)
                                .map(([k, v]) => `${k}=${v}`)
                                .join("|")}
                            </td>
                            <td>{fmtNum(row.delta_pass_rate)}</td>
                            <td>{fmtNum(row.delta_mean_score)}</td>
                            <td>{fmtMs(row.delta_mean_wall_ms)}</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </>
              )}
            </>
          )}
        </div>
      )}
    </section>
  );
}

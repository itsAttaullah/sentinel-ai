export type Project = {
  id: string;
  name: string;
  description?: string | null;
  created_at: string;
};

export type MetricsSummary = {
  wall_ms?: number | null;
  estimated_cost_usd?: number | null;
  tokens_in?: number;
  tokens_out?: number;
  retry_count?: number;
};

export type RunSummary = {
  run_id: string;
  name?: string | null;
  agent_name?: string | null;
  agent_version?: string | null;
  status: string;
  started_at?: string | null;
  ended_at?: string | null;
  tags?: string[] | null;
  metrics_summary?: MetricsSummary | null;
};

export type RunMetrics = {
  wall_ms?: number | null;
  span_total_ms?: number;
  attribution_ms?: Record<string, number>;
  attribution_share?: Record<string, number>;
  tokens?: { in: number; out: number; total: number };
  estimated_cost_usd?: number;
  retry_count?: number;
  error_event_count?: number;
  span_counts?: Record<string, number>;
  span_error_count?: number;
  status?: string;
  pricing_table_version?: string;
  currency?: string;
  notes?: string[];
};

export type Span = {
  schema_version?: string;
  project_id?: string;
  run_id?: string;
  span_id: string;
  parent_span_id?: string | null;
  kind: string;
  name: string;
  status: string;
  started_at?: string | null;
  ended_at?: string | null;
  llm?: Record<string, unknown>;
  tool?: Record<string, unknown>;
  planner?: Record<string, unknown>;
  memory?: Record<string, unknown>;
  error?: Record<string, unknown>;
};

export type TraceEvent = {
  event_id: string;
  type: string;
  timestamp?: string | null;
  message?: string | null;
  span_id?: string | null;
  level?: string | null;
};

export type RunDetail = {
  run: {
    run_id: string;
    name?: string | null;
    agent_name?: string | null;
    agent_version?: string | null;
    status: string;
    started_at?: string | null;
    ended_at?: string | null;
    tags?: string[] | null;
    error?: Record<string, unknown> | null;
  };
  spans?: Span[];
  events?: TraceEvent[];
  metrics?: RunMetrics | null;
};

export type ProjectMetrics = {
  project_id: string;
  run_count: number;
  success_count: number;
  success_rate: number | null;
  wall_ms: { avg: number | null; p50: number | null; p95: number | null };
  total_estimated_cost_usd: number;
  total_tokens: { in: number; out: number; total: number };
  total_retries: number;
  attribution_ms_total: Record<string, number>;
};

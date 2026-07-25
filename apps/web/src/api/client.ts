import type { Project, ProjectMetrics, RunDetail, RunSummary } from "./types";

const API_BASE = (import.meta.env.VITE_API_URL as string | undefined)?.replace(/\/$/, "") ?? "";

async function request<T>(path: string): Promise<T> {
  const response = await fetch(`${API_BASE}${path}`, {
    headers: { Accept: "application/json" },
  });
  if (!response.ok) {
    let detail = response.statusText;
    try {
      const body = await response.json();
      detail = body?.detail?.error?.message ?? body?.error?.message ?? detail;
    } catch {
      /* ignore */
    }
    throw new Error(`${response.status}: ${detail}`);
  }
  return response.json() as Promise<T>;
}

export function fetchHealth(): Promise<{ status: string; version?: string }> {
  return request("/healthz");
}

export function fetchProjects(): Promise<{ items: Project[] }> {
  return request("/v1/projects");
}

export function fetchRuns(
  projectId: string,
  opts?: { status?: string; limit?: number },
): Promise<{ items: RunSummary[] }> {
  const params = new URLSearchParams();
  if (opts?.status) params.set("status", opts.status);
  if (opts?.limit) params.set("limit", String(opts.limit));
  const qs = params.toString();
  return request(`/v1/projects/${encodeURIComponent(projectId)}/runs${qs ? `?${qs}` : ""}`);
}

export function fetchRun(
  projectId: string,
  runId: string,
): Promise<RunDetail> {
  return request(
    `/v1/projects/${encodeURIComponent(projectId)}/runs/${encodeURIComponent(runId)}?include=spans,events,metrics`,
  );
}

export function fetchProjectMetrics(projectId: string): Promise<ProjectMetrics> {
  return request(`/v1/projects/${encodeURIComponent(projectId)}/metrics`);
}

import { useEffect, useState } from "react";
import { Navigate, Route, Routes } from "react-router-dom";
import { fetchHealth } from "./api/client";
import { Layout } from "./components/Layout";
import { BenchmarksPage } from "./pages/BenchmarksPage";
import { ProjectsPage } from "./pages/ProjectsPage";
import { RunDetailPage } from "./pages/RunDetailPage";
import { RunsPage } from "./pages/RunsPage";

export default function App() {
  const [health, setHealth] = useState<{ status: string; version?: string } | null>(
    null,
  );
  const [healthError, setHealthError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    fetchHealth()
      .then((data) => {
        if (!cancelled) {
          setHealth(data);
          setHealthError(null);
        }
      })
      .catch((err: Error) => {
        if (!cancelled) {
          setHealth(null);
          setHealthError(err.message);
        }
      });
    return () => {
      cancelled = true;
    };
  }, []);

  return (
    <Layout health={health} healthError={healthError}>
      <Routes>
        <Route path="/" element={<ProjectsPage />} />
        <Route path="/projects/:projectId" element={<RunsPage />} />
        <Route
          path="/projects/:projectId/benchmarks"
          element={<BenchmarksPage />}
        />
        <Route
          path="/projects/:projectId/benchmarks/:benchmarkId"
          element={<BenchmarksPage />}
        />
        <Route
          path="/projects/:projectId/runs/:runId"
          element={<RunDetailPage />}
        />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </Layout>
  );
}

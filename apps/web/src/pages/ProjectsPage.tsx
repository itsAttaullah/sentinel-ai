import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { fetchProjects } from "../api/client";
import type { Project } from "../api/types";

export function ProjectsPage() {
  const [items, setItems] = useState<Project[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    fetchProjects()
      .then((data) => {
        if (!cancelled) setItems(data.items);
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
  }, []);

  return (
    <section>
      <div className="page-head">
        <div>
          <h1>Projects</h1>
          <p className="muted">Select a project to inspect runs and timelines.</p>
        </div>
      </div>

      <div className="panel panel-pad">
        {loading && <div className="loading">Loading projects…</div>}
        {error && (
          <div className="error-box">
            Failed to load projects: {error}. Is the API running on :8080?
          </div>
        )}
        {!loading && !error && items.length === 0 && (
          <div className="empty">
            No projects yet. Upload a batch with the CLI or SDK first.
          </div>
        )}
        {!loading && !error && items.length > 0 && (
          <table className="table">
            <thead>
              <tr>
                <th>Project</th>
                <th>ID</th>
                <th>Created</th>
              </tr>
            </thead>
            <tbody>
              {items.map((project) => (
                <tr key={project.id}>
                  <td>
                    <Link className="row-link" to={`/projects/${project.id}`}>
                      {project.name}
                    </Link>
                    {project.description ? (
                      <div className="muted">{project.description}</div>
                    ) : null}
                  </td>
                  <td className="mono">{project.id}</td>
                  <td className="mono muted">
                    {new Date(project.created_at).toLocaleString()}
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

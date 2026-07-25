import { Link } from "react-router-dom";
import type { ReactNode } from "react";

type Props = {
  children: ReactNode;
  health?: { status: string; version?: string } | null;
  healthError?: string | null;
};

export function Layout({ children, health, healthError }: Props) {
  const ok = !healthError && health?.status === "ok";
  return (
    <div className="app-shell">
      <header className="topbar">
        <Link to="/" className="brand">
          <strong>Sentinel AI</strong>
          <span>Observe · Measure · Compare</span>
        </Link>
        <div className={`health ${ok ? "ok" : "bad"}`}>
          {ok
            ? `API ok${health?.version ? ` · v${health.version}` : ""}`
            : healthError
              ? `API offline`
              : "API…"}
        </div>
      </header>
      {children}
    </div>
  );
}

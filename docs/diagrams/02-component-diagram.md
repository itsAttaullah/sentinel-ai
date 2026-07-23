# Component Diagram

C4 Level 2 — Major building blocks inside Sentinel AI.

```mermaid
flowchart TB
  subgraph Experience
    UI[Web UI]
    CLI[CLI]
    PUB[Public HTTP API]
  end

  subgraph Control["Control & Ingest"]
    GW[Ingest Gateway]
    API[Control Plane]
    AUTH[Auth / API Keys]
  end

  subgraph Async["Async Processing"]
    Q[(Queue)]
    W[Workers]
    MET[Metrics Engine]
    EVL[Evaluation Engine]
    BEN[Benchmark Orchestrator]
  end

  subgraph Data["Data Plane"]
    PG[(PostgreSQL)]
    OBJ[(Object Store)]
  end

  subgraph Edge["External Edge"]
    SDK[SDKs]
    ADP[Adapters]
  end

  ADP --> SDK
  SDK --> GW
  GW --> AUTH
  GW --> Q
  Q --> W
  W --> PG
  W --> OBJ
  W --> MET
  API --> AUTH
  API --> PG
  API --> OBJ
  API --> EVL
  API --> BEN
  EVL --> W
  BEN --> W
  MET --> PG
  UI --> API
  CLI --> API
  PUB --> API
```

## Boundary Notes

- **Adapters** never talk to the database directly.
- **UI** is a client of the Control Plane only.
- **Workers** own derived state (metrics, scores), not interactive request threads.

# sentinel-adapter-conformance

Defines the **official adapter quality bar** (ADR-0007).

```python
from sentinel_adapter_conformance import run_conformance
from sentinel_adapter_custom import CustomAdapter

report = run_conformance(CustomAdapter())
assert report.passed
```

Checks include metadata completeness, schema version alignment, bind/tracer
lifecycle, and emission of canonical run/llm/tool spans via an in-memory exporter.

# sentinel-adapter-custom

Reference adapter for **hand-rolled agents**. Thin helpers around ``Tracer`` that
demonstrate the official plugin shape without framework dependencies.

```python
from sentinel_ai import FileExporter, Tracer
from sentinel_adapter_custom import CustomAdapter

tracer = Tracer(project_id="proj_demo", exporter=FileExporter("out.jsonl"))
adapter = CustomAdapter()
adapter.bind(tracer)

with adapter.start_run(name="task") as run:
    with adapter.llm_span(model="gpt-4.1-mini", provider="openai"):
        pass
    with adapter.tool_span("web_search", input={"q": "sentinel"}):
        pass
```

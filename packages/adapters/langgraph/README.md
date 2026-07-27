# sentinel-adapter-langgraph

Maps LangGraph / LangChain-style callback events into Sentinel traces.

**Core package has no LangGraph dependency.** Normalized events always work.
Optional ``[langchain]`` extra enables a ``BaseCallbackHandler`` subclass.

```python
from sentinel_ai import FileExporter, Tracer
from sentinel_adapter_langgraph import LangGraphAdapter

tracer = Tracer(project_id="proj_demo", exporter=FileExporter("out.jsonl"))
adapter = LangGraphAdapter()
adapter.bind(tracer)

# Feed normalized events (framework-agnostic):
adapter.handle_event({"type": "chain_start", "name": "agent", "run_id": "c1"})
adapter.handle_event({"type": "llm_start", "name": "model", "run_id": "l1", "parent_run_id": "c1",
                      "model": "gpt-4.1-mini", "provider": "openai"})
adapter.handle_event({"type": "llm_end", "run_id": "l1", "tokens_in": 10, "tokens_out": 5})
adapter.handle_event({"type": "chain_end", "run_id": "c1"})
adapter.end_run()
```

With LangChain installed:

```powershell
pip install -e ".\packages\adapters\langgraph[langchain]"
```

```python
handler = adapter.as_callback_handler()  # langchain_core BaseCallbackHandler
# graph.invoke(..., config={"callbacks": [handler]})
```

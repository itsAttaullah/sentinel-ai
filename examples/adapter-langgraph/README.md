# LangGraph adapter example

Feeds **normalized** callback events (no LangGraph package required).

```powershell
pip install -e ".\packages\sdk-python"
pip install -e ".\packages\adapters\base"
pip install -e ".\packages\adapters\langgraph"
python .\examples\adapter-langgraph\main.py
```

For a real LangChain callback handler:

```powershell
pip install -e ".\packages\adapters\langgraph[langchain]"
```

Then `adapter.as_callback_handler()` returns a `BaseCallbackHandler`.

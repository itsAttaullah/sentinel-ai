# Custom adapter example

Reference instrumentation using ``sentinel-adapter-custom``.

```powershell
pip install -e ".\packages\sdk-python"
pip install -e ".\packages\adapters\base"
pip install -e ".\packages\adapters\custom"
python .\examples\adapter-custom\main.py
```

Output JSONL lands in `out/traces.jsonl` by default.

# Agentic Data Visualization — Planner / Coder / Reviewer

Google Colab notebook that uses the [Chocolate Sales Dataset (2023–2024)](https://www.kaggle.com/datasets/ssssws/chocolate-sales-dataset-2023-2024) to generate business visualizations with Plotly.

## Agent workflow

```text
User question
     ↓
Planner Agent → (get_metadata or get_sample)
     ↓
Coder Agent → Python / Plotly code
     ↓
Reviewer Agent → semantic review in LIVE mode
     ↓
Deterministic AST validator → restricted pandas/Plotly operations
     ↓
Executor → chart output
     └── if rejected / runtime error: feedback → Coder (up to MAX_ATTEMPTS)
```

The project **preserves the original Planner, DataTools, Coder, and Plotly Executor**. A separate Reviewer call, deterministic guard, and bounded correction loop are the new changes.

## Run on Google Colab

1. Open [`AgentsVisualForGrad.ipynb`](AgentsVisualForGrad.ipynb) from GitHub with **Open in Colab**, or upload it to [colab.research.google.com](https://colab.research.google.com/).
2. Run all cells in order. The installation cell installs dependencies.
3. By default, `DEMO_MODE = True`, `AUTO_EXECUTE = True`, `MAX_ATTEMPTS = 3`. The **same pipeline** runs end-to-end with deterministic stand-ins for LLM responses and displays a real monthly revenue Plotly chart. This verifies execution but **does not test hosted LLM agents**.
4. To use actual AI agents, create a new Hugging Face access token, add it to **Colab Secrets** under `HF_TOKEN` and enable notebook access; set `DEMO_MODE = False`. Verify and update `PLANNER_MODEL`, `CODER_MODEL`, and `REVIEWER_MODEL` to available hosted chat models. The original notebook referenced `Qwen/Qwen2.5-72B-Instruct` and `deepseek-ai/DeepSeek-V4-Pro`; these identifiers are **not guaranteed available**.
5. Run the example cell; for interactive use you can optionally call `agent.run()`.

## Data source

- Kaggle dataset slug: `ssssws/chocolate-sales-dataset-2023-2024`
- Required files: `sales.csv`, `products.csv`, `stores.csv`, `customers.csv`
- `kagglehub.dataset_download` resolves the current cache directory (no version-specific hard-coded paths).
- CSVs are not committed. Reproducibility also depends on dataset availability/version and the selected inference provider.

## How the correction loop works

- Planner calls **one of the original two DataTools** to inspect the data.
- Coder writes Plotly/pandas Python, assigning the resulting figure to variable `fig`. Coder may **not** call `fig.show()`; the Executor displays validated output.
- Reviewer evaluates code semantics in LIVE mode (dataset columns, aggregation, axes, user intent); a separate static validator rejects dangerous/unsupported Python constructs.
- If review rejects the code or execution raises an error, the reason and previous attempt are sent to Coder for another generation.
- After 3 attempts by default, the system stops with an explicit error instead of looping forever.
- `agent.history` and the returned `result["attempts"]` record attempt status.

## Boundaries and limitations

**This notebook does not provide a secure Python sandbox.** Its AST validator is deliberately strict and reduces accidental or obvious unsafe operations, but the LLM Reviewer and static checks cannot guarantee safe code or accurate charts. Use a disposable Colab runtime, avoid giving it unnecessary secrets, and use real process isolation/resource restrictions before any untrusted production deployment.

The Demo Reviewer does only deterministic checks; it is not a live Reviewer LLM. Live runs require Hugging Face APIs and can fail if model access, pricing, or provider availability changes.

The original notebook had credentials embedded in cells. **No keys are included in this project**; previously exposed keys should be revoked even if you no longer use them.

## Dependencies

See `requirements.txt`. It intentionally lists direct dependencies; record exact tested package versions after a successful Colab run if you need a fully reproducible environment.

## Local regression tests (no hosted LLM calls)

```bash
python tests/test_agent_loop.py
```

Tests exercise Demo pipeline execution, Reviewer rejection feedback, deterministic validator rejection, runtime-error retry, maximum attempts, and a simulated live Planner/Coder/Reviewer API workflow. Tests use in-memory sample data and do not download Kaggle data or invoke Hugging Face.

# Live request budgets

An `LLMClient` without an injected budget shares the process-wide five-request
smoke cap. Mock clients consume zero requests unless a test explicitly enables
live accounting. A real client cannot disable accounting.

For an experiment, construct one explicit finite budget and share it across all
clients, conditions and batches in that run:

```python
from src.llm.client import LLMClient, LiveBudget
from src.baseline.pipeline import BaselinePipeline
from src.rag.pipeline import RAGPipeline

# Count input views, not scenario pairs. Five conditions = No-RAG + four k values.
# Frozen max_retries=3 permits at most four network attempts per prediction.
budget = LiveBudget(max_requests=number_of_views * 5 * 4)
client = LLMClient(live_budget=budget)
baseline = BaselinePipeline(client=client)
rag = RAGPipeline(client=client)
```

The runner supplies `number_of_views` and owns this shared budget. Do not create a
fresh budget per sample or condition. Limits must be non-negative integers; zero
blocks all live requests. No implicit unlimited mode or environment override exists.

Every outer-loop request attempt, including retries, consumes one unit. SDK retries
are disabled to prevent uncounted requests. Parsing a received response consumes
no additional units and does not trigger a retry. Exhaustion prevents dispatch and
returns an `API_FAILURE` execution record with `error_type=LiveBudgetExceededError`
and a reason containing the limit. Model, prompts, schemas and generation settings
are unchanged. `budget.count` and `budget.remaining` expose accounting.

This cap is local to the shared object/process. A multi-process runner must allocate
separate finite portions of its run budget explicitly; provider-side spending limits
remain the cross-process safeguard. This example documents configuration only and
does not start an experiment.

# From Local Inference to Local Agency

A controlled experiment using a local Gemma model, served through Ollama, to repair Python code through the Antigravity SDK.

**Ollama provides local inference. Antigravity SDK provides the agent runtime.** The agent inspects a workspace, runs tests, edits the implementation, and checks the result.

## The experiment

The calculator is a deliberately small test fixture with five operations and one unit test per operation. The starting implementation produces three failing tests. The task prompt supplies the goal and constraints without identifying the fixes.

| Stage | Passing tests | Failing tests |
| --- | --- | --- |
| Starting implementation | 2 | 3 |
| Successful repair | 5 | 0 |

The agent is instructed to leave the tests and runner unchanged, avoid Git operations, and rerun the tests after editing.

## Architecture

- **Python application:** configures the agent, submits the task, and reports execution details.
- **Antigravity SDK:** manages the agent loop, workspace tools, command execution, and tool policies.
- **Ollama:** serves the model through its local OpenAI-compatible API.
- **Gemma:** interprets observations and selects the next action.

The runner uses `gemma4:26b` at `http://localhost:11434/v1` through `LocalOpenAIAgentConfig(...).lightweight()`. See the [official local-model documentation](https://antigravity.google/docs/sdk/local-models/) for the integration.

## Repository layout

| File | Purpose |
| --- | --- |
| `calculator.py` | Implementation the agent repairs |
| `test_calculator.py` | Five fixed acceptance tests |
| `main.py` | Agent runner, telemetry, and independent test verification |
| `pyproject.toml` | Python requirement and dependencies |
| `uv.lock` | Locked dependency versions |
| `.python-version` | Python 3.14 selection |

The `main` branch preserves the broken baseline. The `antigravity-fix` branch contains the recorded repair. [Compare the branches](https://github.com/alfonsmr/antigravity-sdk-demo/compare/main...antigravity-fix).

## Run the experiment

### 1. Prepare the environment

Install Git, [uv](https://docs.astral.sh/uv/getting-started/installation/), and [Ollama](https://docs.ollama.com/quickstart). The project requires Python 3.14 or later and selects Python 3.14 through `.python-version`. The lockfile currently pins `google-antigravity` to `0.1.18`.

Use a machine with enough memory for the selected model and its context. Read the execution-permissions section below before running the agent.

Clone the baseline and create a separate branch for your run:

```bash
git clone --branch main https://github.com/alfonsmr/antigravity-sdk-demo.git
cd antigravity-sdk-demo
git switch -c reproduce-local-agent
uv sync --locked
```

The [locked sync](https://docs.astral.sh/uv/concepts/projects/sync/) checks that dependency metadata matches the lockfile.

### 2. Start Ollama and download the model

Open Ollama, or run the server in a separate terminal if it is not already running:

```bash
ollama serve
```

In your project terminal:

```bash
ollama pull gemma4:26b
ollama list
```

### 3. Verify the baseline

```bash
uv run --locked python -m unittest -v
git status --short
```

Expect **five tests with three failures** and a clean working tree. The failing test command returns a nonzero exit code by design.

### 4. Run the agent

```bash
uv run --locked python main.py
```

The runner prints environment and model information, tool calls and arguments, elapsed time, available token usage, Ollama loaded-model state, and test results before and after the task. The final test run happens outside the agent loop.

### 5. Verify the repair yourself

```bash
uv run --locked python -m unittest -v
git status --short
git diff
```

Expect **five passing tests** and changes only to `calculator.py`. Inspect the full diff to confirm that the tests and runner remain unchanged.

To inspect the recorded repair separately:

```bash
git diff origin/main..origin/antigravity-fix
```

For another attempt, use a fresh clone of `main` so previous repairs do not affect the baseline.

## Execution permissions

The runner uses `policy.allow_all()`, and its pre-tool hook also returns `HookResult(allow=True)`. Tool execution is intentionally permissive.

Run the experiment in a disposable, isolated environment without valuable credentials or data. The prompt's restrictions and the workspace setting do not by themselves sandbox commands. Git records tracked-file changes; it cannot undo arbitrary effects elsewhere on the machine.

## What the result establishes

A successful run demonstrates this model and runtime completing a bounded repair workflow. Five passing tests cover five specific cases; they do not establish general software-engineering reliability or superiority over hosted models.

Local inference does not establish that the entire workflow is offline. The runner's “Remote model API: NO” and “External cloud LLM: NO” messages are configuration labels, not network measurements. Use model identity and Ollama telemetry as supporting evidence, and evaluate network activity separately if isolation matters.

Tool sequences and timing can vary. Token metrics are reported only when the backend supplies them.

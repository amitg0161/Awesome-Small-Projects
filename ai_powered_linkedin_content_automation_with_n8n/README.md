# FinEdge LinkedIn Content Automation

An AutoGen-inspired FastAPI service generates three content ideas, a LinkedIn draft, a heuristic quality score, and hashtags. n8n schedules the run, composes the final text, records an audit trail in SQLite, and routes to Slack review or LinkedIn publishing.

## Architecture

```text
n8n Schedule (weekdays, 09:15 Asia/Kolkata)
  -> Brand Config
  -> AutoGen Microservice (/linkedin)
       Ideation Agent -> Drafting Agent -> Hashtag Agent
  -> Compose Final -> Log Run (/runs)
  -> Approval Gate
       dryRun=true OR confidence below threshold -> Slack Review
       otherwise -> LinkedIn Posts API
  -> Record delivery result (/runs)
```

`AI_MODE=auto` is the default: it uses the OpenAI-compatible provider when `OPENAI_API_KEY` is set, and otherwise sends the three agent requests to local Ollama without an API key. `AI_MODE=ollama` forces Ollama, `AI_MODE=openai` forces the keyed provider, and `AI_MODE=demo` selects deterministic offline output for tests. The returned confidence is a transparent content-quality heuristic, not a probability that claims are true. Human review remains essential for regulated financial content.

## Local setup

Python 3.10 or newer is required.

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
Copy-Item .env.example .env
uvicorn main:app --reload --env-file .env
```

On Ubuntu, use `python3 -m venv .venv`, `source .venv/bin/activate`, and `cp .env.example .env`. The service listens on port 8000. Check `http://127.0.0.1:8000/healthz` and interactive API docs at `http://127.0.0.1:8000/docs`.

### API smoke test

```bash
curl -X POST http://127.0.0.1:8000/linkedin \
  -H 'Content-Type: application/json' \
  -d '{
    "runId":"smoke-test-001",
    "brand":{"name":"FinEdge Mumbai","audience":"Indian finance professionals","tone":"clear and credible","key_principles":["financial inclusion"],"prohibited_claims":["guaranteed returns"]},
    "context":{"topic":"responsible digital finance","key_points":["financial literacy","informed decisions"],"call_to_action":"What would you add to the conversation?","source_notes":"Use only these supplied points."}
  }'
```

Expect HTTP 200 with `ideas` (three strings), `draft`, `confidenceScore` (0 to 1), `hashtags`, and `trace`. Each generated run is persisted automatically. Inspect it at `GET /runs/smoke-test-001`; `POST /runs` upserts the route and delivery status from n8n.

With the default `AI_MODE=auto`, no API key is needed for model calls when Ollama is installed and running. Pull the configured model once with `ollama pull qwen:latest`; set `OLLAMA_MODEL` to a different locally available model if needed. Ollama listens on port 11434 by default. `OLLAMA_TIMEOUT_SECONDS` defaults to 180 because local model startup can be slower than hosted APIs. If Ollama is not reachable or the model is missing and no OpenAI key is configured, `/linkedin` returns an actionable error and records the failed run rather than silently switching to demo text.

Ollama troubleshooting: check installed models with `ollama list` and pull the configured model if the service reports it missing. A 504 indicates the local model exceeded `OLLAMA_TIMEOUT_SECONDS`; increase it, use a smaller model, or lower `OLLAMA_NUM_PREDICT`. The service disables Qwen thinking tokens and strips JSON Markdown fences before parsing agent output.

To use an OpenAI-compatible provider, set `OPENAI_API_KEY` in `.env`; auto mode then prefers it. `OPENAI_BASE_URL` and `OPENAI_MODEL` support compatible providers. For Docker, `127.0.0.1` points inside the service container, so set `OLLAMA_BASE_URL` to a reachable host address such as `http://host.docker.internal:11434` (or the Ollama service name on a shared Docker network). Ollama requests stay on the configured Ollama host; keyed provider calls send brand and source-note data to that provider. Review your organization's data-handling requirements before enabling remote calls.

Set a strong `API_KEY` before exposing the service. Authenticated endpoints require `X-API-Key`; `/healthz` remains public. In n8n, create an **HTTP Header Auth** credential with header `X-API-Key` and the same value, then attach it to the microservice and run-log HTTP nodes.

## n8n setup

1. Import `workflows/linkedin_content_automation.json` in n8n. Keep it inactive while configuring credentials.
2. Open **Brand Config** and replace the sample topic, audience, points, call to action, prohibited claims, confidence threshold, and organization URN. `dryRun` is `true` by default.
3. Update the three service URLs (`/linkedin` and `/runs`) to an address reachable from n8n. `host.docker.internal` is convenient on Docker Desktop; on a Linux VM, use the service/container DNS name or configure the Docker host gateway. If n8n runs directly on the VM, use `http://127.0.0.1:8000`.
4. Attach the HTTP Header Auth credential to each service HTTP node.
5. Configure **Slack Review** with a Slack API credential and the review channel ID. This is a Slack OAuth/API integration, not an incoming webhook.
6. For live posting only, configure the LinkedIn OAuth2 credential with the required organization-posting access, replace the LinkedIn version placeholder with a version currently supported by LinkedIn, and set a real organization URN. Keep `dryRun=true` until a full end-to-end dry run succeeds.
7. Execute nodes in order: Brand Config, AutoGen Microservice, Compose Final, Log Run, Approval Gate, and the Slack branch. Then run the whole workflow manually. Inspect n8n execution data and `GET /runs/<runId>` before considering live posting.
8. Set `dryRun=false` only when ready. A confidence score below `minConfidence` still routes to Slack; only a non-dry-run score at or above the threshold reaches LinkedIn. Activate the schedule after a supervised full run.

The schedule is weekdays at 09:15 in `Asia/Kolkata`; edit the Schedule Trigger if the organization's cadence differs. n8n execution history is enabled for success and error data, and outbound nodes retry transient failures three times. A failed delivery leaves the last recorded status (`queued_for_review` or `queued_for_linkedin`) visible in SQLite and the failed execution visible in n8n.

### LinkedIn OAuth notes

The live node targets `POST https://api.linkedin.com/rest/posts` and uses the current organization URN and API-version header. LinkedIn access is subject to app approval, product access, scopes, and organization role permissions. LinkedIn changes version requirements; use a currently supported `YYYYMM` value when configuring the node. Do not test against a real organization until the dry-run route and permissions have been independently reviewed.

## VM deployment

The service can run under a process manager or Docker. For Docker, build with `docker build -t finedge-linkedin-service .` and run with a persistent volume mounted at `/app/data`; pass environment variables through your secret manager. Configure `OLLAMA_BASE_URL` to a container-reachable Ollama host when using local inference. Do not publish port 8000 directly to the public internet. Put it behind a TLS reverse proxy and require `API_KEY`. n8n must be able to reach the private service address.

For a direct Ubuntu process, install requirements in a virtual environment and run `uvicorn main:app --host 0.0.0.0 --port 8000 --env-file .env` under systemd or another supervisor. Restrict network access to the n8n host and preserve the configured SQLite directory across restarts.

## Logging and safety

- SQLite stores run ID, timestamps, status, composed text, confidence, dry-run flag, route, and error text. Updates use the run ID as an upsert key.
- Standard application logs include run IDs and the selected mode; API secrets and request bodies are not logged.
- n8n stores execution input/output and failure history. Protect n8n access and set an appropriate retention policy because execution data contains draft content.
- The score checks length, topic/CTA presence, key-point coverage, and prohibited phrases. It does not verify factual accuracy, legal compliance, or suitability for publication.
- The gate is a confidence/dry-run router, not an interactive human-approval callback. Low-score and dry-run drafts are delivered to Slack for a person to review; live high-score posts publish directly when dry run is disabled.

## Tests and evidence

Run the local service and workflow artifact tests with:

```bash
python -m pytest -q
```

The tests cover the structured response, SQLite persistence/upsert, API-key enforcement, validation errors, and workflow routing. The included screenshot directory records local test evidence when captured. This workspace has no configured VM, n8n instance, Slack credential, or LinkedIn credential, so those external integrations must be exercised in the target environment; no live workflow execution is claimed here.

Local evidence: `screenshots/api-success.png` captures Swagger UI executing `POST /linkedin` with HTTP 200. The response contained three ideas, a draft, confidence `0.94`, and four hashtags; the corresponding run was persisted and retrievable from `/runs/screenshot-smoke-20261014`. Nine automated tests pass locally. A separate live no-key test used Ollama `qwen:latest`; all three agent calls returned HTTP 200 and `/linkedin` succeeded with run ID `ollama-live-smoke-final`. No n8n node or end-to-end workflow screenshot is included because no n8n instance is connected to this workspace.

## Reflection

The three agent roles are separated so each stage has a narrow prompt and a traceable output, while the implementation avoids requiring an orchestration library for a small, inspectable pipeline. Auto mode supports keyless local Ollama while preferring a configured hosted provider; deterministic demo mode keeps tests repeatable. Local inference trades cloud-provider cost and data transfer for host compute, model management, and latency. A heuristic confidence score is useful for routing but is deliberately labeled as non-probabilistic. Slack-first dry runs, explicit thresholding, a persistent run log, and an inactive imported workflow reduce accidental publishing risk. The principal trade-off is that Slack review is a notification, not a workflow-based approval callback; adding interactive approval would require a signed Slack action endpoint and a second n8n trigger.
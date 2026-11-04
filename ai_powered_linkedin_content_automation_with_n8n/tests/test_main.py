import json

from fastapi.testclient import TestClient

import main


def sample_payload(run_id: str = "test-run-1") -> dict:
    return {
        "runId": run_id,
        "brand": {
            "name": "FinEdge Mumbai",
            "audience": "Indian finance professionals",
            "tone": "clear, credible, and human",
            "key_principles": ["make financial information accessible"],
            "prohibited_claims": ["guaranteed returns"],
        },
        "context": {
            "topic": "responsible digital finance",
            "key_points": ["financial literacy", "informed decisions"],
            "call_to_action": "What would you add to the conversation?",
            "source_notes": "",
        },
    }


def test_linkedin_generates_structured_content_and_persists_run(tmp_path, monkeypatch):
    monkeypatch.setenv("AI_MODE", "demo")
    monkeypatch.setenv("AUTOMATION_DB_PATH", str(tmp_path / "runs.db"))
    monkeypatch.delenv("API_KEY", raising=False)

    with TestClient(main.app) as client:
        response = client.post("/linkedin", json=sample_payload())

        assert response.status_code == 200
        body = response.json()
        assert body["runId"] == "test-run-1"
        assert len(body["ideas"]) == 3
        assert isinstance(body["draft"], str) and body["draft"]
        assert 0 <= body["confidenceScore"] <= 1
        assert body["hashtags"] and all(tag.startswith("#") for tag in body["hashtags"])
        assert body["trace"]["mode"] == "demo"

        stored = client.get("/runs/test-run-1")
        assert stored.status_code == 200
        assert stored.json()["status"] == "generated"
        assert "#" in stored.json()["finalText"]


def test_run_updates_are_upserted(tmp_path, monkeypatch):
    monkeypatch.setenv("AUTOMATION_DB_PATH", str(tmp_path / "runs.db"))
    monkeypatch.delenv("API_KEY", raising=False)
    update = {
        "runId": "route-1",
        "status": "sent_to_slack",
        "finalText": "review this draft",
        "confidenceScore": 0.82,
        "dryRun": True,
        "route": "slack",
    }

    with TestClient(main.app) as client:
        first = client.post("/runs", json=update)
        second = client.post("/runs", json={**update, "status": "approved"})

    assert first.status_code == second.status_code == 200
    assert second.json()["status"] == "approved"


def test_api_key_is_enforced_when_configured(monkeypatch):
    monkeypatch.setenv("AI_MODE", "demo")
    monkeypatch.setenv("API_KEY", "local-test-secret")
    with TestClient(main.app) as client:
        missing_key = client.post("/linkedin", json=sample_payload())
        valid_key = client.post(
            "/linkedin",
            json=sample_payload("protected-run"),
            headers={"X-API-Key": "local-test-secret"},
        )

    assert missing_key.status_code == 401
    assert valid_key.status_code == 200


def test_invalid_request_is_rejected():
    with TestClient(main.app) as client:
        response = client.post("/linkedin", json={"brand": {}, "context": {}})
    assert response.status_code == 422


def test_generation_failure_is_persisted(tmp_path, monkeypatch):
    monkeypatch.setenv("AI_MODE", "openai")
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.setenv("AUTOMATION_DB_PATH", str(tmp_path / "runs.db"))
    monkeypatch.delenv("API_KEY", raising=False)

    with TestClient(main.app) as client:
        failed = client.post("/linkedin", json=sample_payload("failed-run"))
        stored = client.get("/runs/failed-run")

    assert failed.status_code == 503
    assert stored.status_code == 200
    assert stored.json()["status"] == "generation_failed"
    assert "OPENAI_API_KEY" in stored.json()["error"]


def test_prohibited_claim_lowers_confidence_below_publish_threshold():
    brand = main.BrandConfig(
        name="FinEdge Mumbai",
        audience="finance professionals",
        prohibited_claims=["guaranteed returns"],
    )
    context = main.PostContext(
        topic="digital finance",
        key_points=["financial literacy"],
        call_to_action="Join the discussion.",
    )
    draft = "Digital finance helps financial literacy. Join the discussion. Guaranteed returns are never appropriate."

    assert main.quality_score(draft, brand, context) < 0.82


def test_agent_json_accepts_ollama_markdown_fences():
    assert main.parse_agent_json('```json\n{"ideas": ["one"]}\n```') == {"ideas": ["one"]}


def test_auto_mode_uses_ollama_without_openai_key(tmp_path, monkeypatch):
    monkeypatch.setenv("AI_MODE", "auto")
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.setenv("OLLAMA_BASE_URL", "http://ollama.test:11434")
    monkeypatch.setenv("OLLAMA_MODEL", "llama3.1:8b")
    monkeypatch.setenv("AUTOMATION_DB_PATH", str(tmp_path / "runs.db"))
    monkeypatch.delenv("API_KEY", raising=False)
    requests = []

    class MockOllamaClient:
        def __init__(self, timeout):
            self.timeout = timeout

        async def __aenter__(self):
            return self

        async def __aexit__(self, *args):
            return None

        async def post(self, url, json, headers=None):
            requests.append((url, json, headers))
            system_prompt = json["messages"][0]["content"]
            if "Ideation Agent" in system_prompt:
                content = {"ideas": ["Idea one", "Idea two", "Idea three"]}
            elif "Drafting Agent" in system_prompt:
                content = {"draft": "A practical post about responsible digital finance. What do you think?"}
            else:
                content = {"hashtags": ["#Fintech", "#DigitalFinance", "#FinancialLiteracy"]}
            return main.httpx.Response(
                200,
                json={"message": {"content": json_module.dumps(content)}},
                request=main.httpx.Request("POST", url),
            )

    json_module = json
    monkeypatch.setattr(main.httpx, "AsyncClient", MockOllamaClient)
    assert main.resolve_ai_mode() == "ollama"

    with TestClient(main.app) as client:
        response = client.post("/linkedin", json=sample_payload("ollama-run"))

    assert response.status_code == 200
    assert response.json()["trace"]["mode"] == "ollama"
    assert len(requests) == 3
    assert all(url == "http://ollama.test:11434/api/chat" for url, _, _ in requests)
    assert all(payload["model"] == "llama3.1:8b" and payload["format"] == "json" for _, payload, _ in requests)
    assert all(payload["think"] is False and payload["options"]["num_predict"] == 512 for _, payload, _ in requests)
    assert all(headers is None for _, _, headers in requests)

    monkeypatch.setenv("OPENAI_API_KEY", "configured")
    assert main.resolve_ai_mode() == "openai"
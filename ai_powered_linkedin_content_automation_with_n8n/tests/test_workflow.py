import json
from pathlib import Path


def test_workflow_requires_approval_and_guards_publishing():
    workflow_path = Path(__file__).parents[1] / "workflows" / "linkedin_content_automation.json"
    workflow = json.loads(workflow_path.read_text(encoding="utf-8"))
    nodes = {node["name"]: node for node in workflow["nodes"]}
    connections = workflow["connections"]

    assert {
        "Schedule Trigger",
        "Brand Config",
        "AutoGen Microservice",
        "Compose Final",
        "Log Run",
        "Slack Review",
        "Approval Gate",
        "Record Approval",
        "Record Review Decision",
        "Publish to LinkedIn",
    } <= nodes.keys()
    assert connections["Log Run"]["main"][0][0]["node"] == "Slack Review"
    assert connections["Slack Review"]["main"][0][0]["node"] == "Approval Gate"
    assert connections["Approval Gate"]["main"][0][0]["node"] == "Record Approval"
    assert connections["Approval Gate"]["main"][1][0]["node"] == "Record Review Decision"
    assert connections["Record Approval"]["main"][0][0]["node"] == "Publish to LinkedIn"

    approval = nodes["Slack Review"]["parameters"]
    assert approval["operation"] == "sendAndWait"
    assert approval["responseType"] == "approval"
    assert approval["approvalOptions"]["values"]["approvalType"] == "double"
    assert approval["captureResponder"] is True
    assert "approverUserIds" in approval["approvers"]

    publish_guard = nodes["Approval Gate"]["parameters"]["conditions"]["conditions"][0]["leftValue"]
    assert ".json.data.approved === true" in publish_guard
    assert "dryRun" in publish_guard
    assert "confidenceScore" in publish_guard
    assert nodes["Publish to LinkedIn"]["retryOnFail"] is False
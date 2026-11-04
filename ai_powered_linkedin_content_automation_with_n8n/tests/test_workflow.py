import json
from pathlib import Path


def test_workflow_has_guarded_dry_run_routes():
    workflow_path = Path(__file__).parents[1] / "workflows" / "linkedin_content_automation.json"
    workflow = json.loads(workflow_path.read_text(encoding="utf-8"))
    nodes = {node["name"]: node for node in workflow["nodes"]}
    connections = workflow["connections"]

    assert {"Schedule Trigger", "Brand Config", "AutoGen Microservice", "Compose Final", "Approval Gate"} <= nodes.keys()
    assert {"Log Run", "Slack Review", "Publish to LinkedIn"} <= nodes.keys()
    assert connections["Approval Gate"]["main"][0][0]["node"] == "Slack Review"
    assert connections["Approval Gate"]["main"][1][0]["node"] == "Publish to LinkedIn"
    assert nodes["Brand Config"]["parameters"]["assignments"]["assignments"]
import json
from pathlib import Path


def export_actions(actions, summary_data=None):
    """
    Exports action payloads to output/recommendations.json 
    and summary metrics to output/summary.json.
    """
    Path("output").mkdir(exist_ok=True)

    with open("output/recommendations.json", "w", encoding="utf-8") as f:
        json.dump(actions, f, indent=2)

    if summary_data:
        with open("output/summary.json", "w", encoding="utf-8") as f:
            json.dump({"summary": summary_data}, f, indent=2)
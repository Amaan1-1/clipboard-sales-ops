import os
import requests
from dotenv import load_dotenv
from flask import Flask, render_template_string, redirect, url_for
from app.database import init_db, get_connection

load_dotenv()

API_BASE = os.getenv("CRM_API_BASE")
API_TOKEN = os.getenv("CRM_API_TOKEN")

HEADERS = {
    "Authorization": f"Bearer {API_TOKEN}",
    "Content-Type": "application/json",
}

app = Flask(__name__)
init_db()

HTML = """
<!DOCTYPE html>
<html>
<head><title>Review Queue</title></head>
<body style="font-family: Arial, sans-serif; margin: 40px; background: #f9f9f9;">
<h1>Review Queue</h1>

{% for proposal in proposals %}
<div style="border:1px solid #ccc; border-radius: 6px; padding:15px; margin:15px 0; background: white;">
    <h3>{{ proposal['facility_name'] }}</h3>

    <p><b>Action:</b> <code>{{ proposal['action'] }}</code></p>

    <p><b>Details:</b> {{ proposal['details'] }}</p>

    <p><b>Status:</b> {{ proposal['status'] }}</p>

    {% if proposal['status'] == 'pending' %}
    <div style="margin-top: 10px;">
        <a href="{{ url_for('approve', proposal_id=proposal['proposal_id']) }}" style="background: green; color: white; padding: 8px 12px; text-decoration: none; border-radius: 4px; font-weight: bold;">Approve & Sync</a>
        <a href="{{ url_for('reject', proposal_id=proposal['proposal_id']) }}" style="background: red; color: white; padding: 8px 12px; text-decoration: none; border-radius: 4px; margin-left: 10px; font-weight: bold;">Reject</a>
    </div>
    {% endif %}
</div>
{% endfor %}
</body>
</html>
"""


def get_parent_id():
    """Fetch the Bellhaven Parent Account ID dynamically."""
    res = requests.get(f"{API_BASE}/accounts?q=Bellhaven Senior Living", headers=HEADERS)
    if res.ok and res.json().get("data"):
        for acc in res.json()["data"]:
            if acc["name"] == "Bellhaven Senior Living (Parent Account)":
                return acc["account_id"]
    return None


def execute_api_call(proposal):
    """Executes CRM API updates when a proposal is approved."""
    action = proposal["action"]
    p_id = proposal["proposal_id"]
    fac_name = proposal["facility_name"]

    parent_id = get_parent_id()
    if not parent_id:
        print("Error: Could not locate Bellhaven Parent Account ID.")
        return False

    try:
        if action == "reparent_account":
            acc_id = p_id.replace("reparent_", "")
            res = requests.patch(f"{API_BASE}/accounts/{acc_id}", headers=HEADERS, json={"parent_id": parent_id})
            return res.ok

        elif action == "rename_account":
            acc_id = p_id.replace("rename_", "")
            res = requests.patch(f"{API_BASE}/accounts/{acc_id}", headers=HEADERS, json={"name": fac_name})
            return res.ok

        elif action == "chow_create_new_account":
            acc_id = p_id.replace("chow_", "")
            res = requests.post(
                f"{API_BASE}/accounts",
                headers=HEADERS,
                json={"name": fac_name, "parent_id": parent_id, "status": "Active"}
            )
            if res.ok:
                new_id = res.json().get("account_id")
                res_patch = requests.patch(
                    f"{API_BASE}/accounts/{acc_id}",
                    headers=HEADERS,
                    json={"chow_current_account": new_id}
                )
                return res_patch.ok
            return False

        elif action == "create_account":
            res = requests.post(
                f"{API_BASE}/accounts",
                headers=HEADERS,
                json={"name": fac_name, "parent_id": parent_id, "status": "Active"}
            )
            return res.ok

        elif action == "mark_duplicate":
            ids = p_id.replace("duplicate_", "").split("_to_")
            if len(ids) == 2:
                loser_id, survivor_id = ids
                res = requests.patch(
                    f"{API_BASE}/accounts/{loser_id}",
                    headers=HEADERS,
                    json={"status": "Inactive", "duplicate_of_account": survivor_id}
                )
                return res.ok
            return False

    except Exception as e:
        print(f"API Error during sync: {e}")
        return False

    return False


@app.route("/")
def index():
    conn = get_connection()
    proposals = conn.execute("SELECT * FROM proposals").fetchall()
    conn.close()

    return render_template_string(HTML, proposals=proposals)


@app.route("/approve/<proposal_id>")
def approve(proposal_id):
    conn = get_connection()
    proposal = conn.execute("SELECT * FROM proposals WHERE proposal_id = ?", (proposal_id,)).fetchone()

    if proposal and proposal["status"] == "pending":
        success = execute_api_call(dict(proposal))
        if success:
            conn.execute("UPDATE proposals SET status = 'approved' WHERE proposal_id = ?", (proposal_id,))
            conn.commit()

    conn.close()
    return redirect(url_for("index"))


@app.route("/reject/<proposal_id>")
def reject(proposal_id):
    conn = get_connection()
    conn.execute("UPDATE proposals SET status = 'rejected' WHERE proposal_id = ?", (proposal_id,))
    conn.commit()
    conn.close()
    return redirect(url_for("index"))


if __name__ == "__main__":
    app.run(debug=True)
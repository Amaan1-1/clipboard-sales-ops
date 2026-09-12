from app.proposal import add_proposal
from app.matcher import normalize_text

BELLHAVEN_PARENT_NAME = "Bellhaven Senior Living (Parent Account)"


def create_action_objects(item):
    """
    Generate standardized action payloads based on pipeline detection rules.
    """
    community = item.get("community", {})
    account = item.get("account")
    match_data = item.get("match", {})
    actions = []

    # 1. Missing CRM account
    if match_data.get("classification") == "missing_crm_account":
        slug = community["name"].lower().replace(" ", "_")
        actions.append({
            "proposal_id": f"create_{slug}",
            "facility_name": community["name"],
            "action": "create_account",
            "account_id": None,
            "details": f"Create new account for '{community['name']}' at {community['street']}, {community['city']}, {community['state']}.",
            "reason": "Website facility missing from CRM."
        })
        return actions

    if not account:
        return actions

    # 2. Rebranding Issue
    if community.get("name") and account.get("name"):
        if normalize_text(community["name"]) != normalize_text(account["name"]):
            actions.append({
                "proposal_id": f"rename_{account['account_id']}",
                "facility_name": community["name"],
                "action": "rename_account",
                "account_id": account["account_id"],
                "details": f"Rename CRM account '{account['name']}' to '{community['name']}'.",
                "reason": "Website facility name differs but address matches exactly."
            })

    # 3. Ownership / Parent Issue
    if account.get("parent_name") != BELLHAVEN_PARENT_NAME:
        revenue = float(account.get("lifetime_revenue", 0) or 0)
        ar = float(account.get("outstanding_ar", 0) or 0)

        # STRICT SOP: CHOW required ONLY if revenue > 0 AND ar > 0
        if revenue > 0 and ar > 0:
            actions.append({
                "proposal_id": f"chow_{account['account_id']}",
                "facility_name": community["name"],
                "action": "chow_create_new_account",
                "account_id": account["account_id"],
                "details": f"Preserve historical account '{account['name']}' (Rev: ${revenue:.2f}, AR: ${ar:.2f}) under old parent '{account['parent_name']}'. Create new account under '{BELLHAVEN_PARENT_NAME}'.",
                "reason": "Account contains revenue AND AR history > 0. Preserve original ownership record."
            })
        else:
            actions.append({
                "proposal_id": f"reparent_{account['account_id']}",
                "facility_name": community["name"],
                "action": "reparent_account",
                "account_id": account["account_id"],
                "details": f"Re-parent existing account '{account['name']}' to '{BELLHAVEN_PARENT_NAME}'.",
                "reason": "Does not meet both revenue and AR requirements for CHOW preservation."
            })

    return actions


def process_duplicates(accounts):
    """
    Find exact name matches, keep the one with the highest revenue active, 
    and mark the others as duplicates.
    """
    from collections import defaultdict
    
    by_name = defaultdict(list)
    for account in accounts:
        name = account["name"].strip().lower()
        if "bellhaven" in name:
            by_name[name].append(account)
            
    duplicate_actions = []
    
    for name, records in by_name.items():
        if len(records) > 1:
            # Sort by highest revenue to pick the surviving account
            records = sorted(records, key=lambda x: float(x.get("lifetime_revenue", 0) or 0), reverse=True)
            survivor = records[0]
            
            for loser in records[1:]:
                action = {
                    "proposal_id": f"duplicate_{loser['account_id']}_to_{survivor['account_id']}",
                    "facility_name": loser["name"],
                    "action": "mark_duplicate",
                    "account_id": loser["account_id"],
                    "details": f"Merge into survivor ({survivor['account_id']}). Mark this record Inactive.",
                    "reason": "Multiple CRM records with the exact same name."
                }
                duplicate_actions.append(action)
                
    return duplicate_actions


def process_pipeline_matches(matches, accounts):
    all_actions = []

    # 1. Process matching/missing logic
    for item in matches:
        actions = create_action_objects(item)
        for action in actions:
            all_actions.append(action)

    # 2. Process duplicates
    dup_actions = process_duplicates(accounts)
    all_actions.extend(dup_actions)

    # 3. Add to Database
    for action in all_actions:
        add_proposal(
            proposal_id=action["proposal_id"],
            facility_name=action["facility_name"],
            action=action["action"],
            details=action["details"]
        )

    return all_actions
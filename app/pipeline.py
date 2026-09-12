from collections import defaultdict

from app.crm import get_accounts
from app.scraper import scrape_communities
from app.matcher import find_match, normalize_address
from app.actions import process_pipeline_matches
from app.export import export_actions
from app.database import init_db


BELLHAVEN_PARENT_NAME = "Bellhaven Senior Living (Parent Account)"


def run_diagnostic():
    print("Loading CRM accounts...")
    accounts = get_accounts()

    print("Scraping Bellhaven website...")
    communities = scrape_communities()

    # Ignore the unexpected non-Bellhaven page for now.
    website_communities = [
        c for c in communities
        if "bellhaven" in c["name"].lower()
    ]

    print(f"\nCRM accounts: {len(accounts)}")
    print(f"Website pages found: {len(communities)}")
    print(f"Bellhaven facilities: {len(website_communities)}")

    # Find Bellhaven parent account.
    parent_accounts = [
        a for a in accounts
        if a["name"] == BELLHAVEN_PARENT_NAME
    ]

    bellhaven_parent = parent_accounts[0] if parent_accounts else None

    if bellhaven_parent:
        print(
            f"\nBellhaven parent ID: "
            f"{bellhaven_parent['account_id']}"
        )

    # ---------------------------------------------------------
    # 1. Match website facilities to CRM
    # ---------------------------------------------------------

    matches = []

    for community in website_communities:
        match = find_match(community, accounts)

        account = match["account"]

        matches.append({
            "community": community,
            "match": match,
            "account": account,
        })

    # ---------------------------------------------------------
    # 2. Show parent problems
    # ---------------------------------------------------------

    print("\n" + "=" * 70)
    print("PARENT ISSUES")
    print("=" * 70)

    for item in matches:
        account = item["account"]

        if not account:
            continue

        if account["parent_name"] != BELLHAVEN_PARENT_NAME:
            print(
                f"\n{item['community']['name']}"
            )
            print(f"  CRM ID: {account['account_id']}")
            print(f"  Current parent: {account['parent_name']}")
            print(f"  Revenue: ${account['lifetime_revenue']}")
            print(f"  Outstanding AR: ${account['outstanding_ar']}")

            if (
                float(account["lifetime_revenue"]) > 0
                and float(account["outstanding_ar"]) > 0
            ):
                print("  ACTION: CHOW — preserve old account + create new account")
            else:
                print("  ACTION: Re-parent existing account")

    # ---------------------------------------------------------
    # 3. Show care-type differences
    # ---------------------------------------------------------

    print("\n" + "=" * 70)
    print("CARE TYPE CHECK")
    print("=" * 70)

    care_map = {
        "assisted living": {"assisted living"},
        "memory support": {"memory care"},
        "short-term rehabilitation & nursing": {"skilled nursing"},
    }

    for item in matches:
        account = item["account"]

        if not account:
            continue

        website_types = {
            x.lower().strip()
            for x in item["community"]["care_offerings"]
        }

        crm_type = (account["care_type"] or "").lower().strip()

        expected = set()

        for website_type in website_types:
            expected.update(care_map.get(website_type, {website_type}))

        if crm_type not in expected:
            print(f"\n{item['community']['name']}")
            print(f"  CRM care type: {account['care_type']}")
            print(
                f"  Website care type: "
                f"{', '.join(item['community']['care_offerings'])}"
            )

    # ---------------------------------------------------------
    # 4. Find duplicate CRM records
    # ---------------------------------------------------------

    print("\n" + "=" * 70)
    print("POTENTIAL DUPLICATES")
    print("=" * 70)

    by_name = defaultdict(list)

    for account in accounts:
        name = account["name"].strip().lower()

        if "bellhaven" in name:
            by_name[name].append(account)

    for name, records in by_name.items():
        if len(records) > 1:
            print(f"\n{name}")

            for account in records:
                print(
                    f"  {account['account_id']} | "
                    f"{account['name']} | "
                    f"{account['billing_street']}, "
                    f"{account['billing_city']}, "
                    f"{account['billing_state']} "
                    f"{account['billing_zip']} | "
                    f"Revenue ${account['lifetime_revenue']} | "
                    f"AR ${account['outstanding_ar']} | "
                    f"Status {account['status']}"
                )

    # ---------------------------------------------------------
    # 5. Find Bellhaven CRM accounts missing from website
    # ---------------------------------------------------------

    print("\n" + "=" * 70)
    print("CRM BELLHAVEN ACCOUNTS NOT FOUND ON WEBSITE")
    print("=" * 70)

    website_addresses = {
        normalize_address(
            f"{c['street']} {c['city']} "
            f"{c['state']} {c['zip']}"
        )
        for c in website_communities
    }

    for account in accounts:
        if account["parent_name"] != BELLHAVEN_PARENT_NAME:
            continue

        crm_address = normalize_address(
            f"{account['billing_street']} "
            f"{account['billing_city']} "
            f"{account['billing_state']} "
            f"{account['billing_zip']}"
        )

        if crm_address not in website_addresses:
            print(
                f"\n{account['account_id']} | "
                f"{account['name']}"
            )
            print(
                f"  Address: {account['billing_street']}, "
                f"{account['billing_city']}, "
                f"{account['billing_state']} "
                f"{account['billing_zip']}"
            )
            print(f"  Revenue: ${account['lifetime_revenue']}")
            print(f"  Outstanding AR: ${account['outstanding_ar']}")
            print(f"  Status: {account['status']}")

    # ---------------------------------------------------------
    # 6. Missing CRM accounts
    # ---------------------------------------------------------

    print("\n" + "=" * 70)
    print("WEBSITE FACILITIES MISSING FROM CRM")
    print("=" * 70)

    for item in matches:
        if item["match"]["classification"] == "missing_crm_account":
            community = item["community"]

            print(
                f"\n{community['name']}"
            )
            print(
                f"  {community['street']}, "
                f"{community['city']}, "
                f"{community['state']} "
                f"{community['zip']}"
            )
            print(
                f"  Care: "
                f"{', '.join(community['care_offerings'])}"
            )

    return matches, accounts


if __name__ == "__main__":
    init_db()
    matches, accounts = run_diagnostic()
    actions = process_pipeline_matches(matches, accounts)

    action_counts = defaultdict(int)
    for act in actions:
        action_counts[act["action"]] += 1

    summary = {
        "crm_accounts": len(accounts),
        "website_facilities": len(matches),
        "create_accounts": action_counts["create_account"],
        "rename_accounts": action_counts["rename_account"],
        "reparent_accounts": action_counts["reparent_account"],
        "chow_accounts": action_counts["chow_create_new_account"],
        "duplicates": action_counts["mark_duplicate"]
    }

    print(f"\nGenerated {len(actions)} action proposals.")
    export_actions(actions, summary)
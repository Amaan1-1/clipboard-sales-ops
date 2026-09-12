import os
import requests
from dotenv import load_dotenv

load_dotenv()

API_BASE = os.getenv("CRM_API_BASE")
API_TOKEN = os.getenv("CRM_API_TOKEN")

HEADERS = {
    "Authorization": f"Bearer {API_TOKEN}",
    "Accept": "application/json",
}


def get_accounts(page_size=50):
    """Retrieve all CRM accounts."""
    accounts = []
    page = 1

    while True:
        response = requests.get(
            f"{API_BASE}/accounts",
            headers=HEADERS,
            params={
                "page": page,
                "page_size": page_size,
            },
            timeout=30,
        )
        response.raise_for_status()

        result = response.json()
        accounts.extend(result["data"])

        if len(accounts) >= result["total"]:
            break

        page += 1

    return accounts


if __name__ == "__main__":
    accounts = get_accounts()
    print(f"Retrieved {len(accounts)} CRM accounts.")

    for account in accounts[:5]:
        print(
            account["account_id"],
            "|",
            account["name"],
            "|",
            account["billing_city"],
            "|",
            account["billing_state"],
        )
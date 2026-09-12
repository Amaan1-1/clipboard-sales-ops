import re


def normalize_text(value):
    """Normalize text for name comparison."""
    if not value:
        return ""

    value = value.lower().strip()

    # Convert symbols before stripping punctuation
    value = value.replace("&", " and ")

    replacements = {
        "centre": "center",
        "healthcare": "health care",
        "rehabilitation": "rehab",
        "the arbors": "arbors",
        " at ": " ",
        " of ": " ",
    }

    for old, new in replacements.items():
        value = value.replace(old, new)

    value = re.sub(r"[^a-z0-9 ]", " ", value)
    value = re.sub(r"\s+", " ", value)

    return value.strip()


def normalize_address(value):
    """Normalize common address abbreviations."""
    if not value:
        return ""

    value = value.lower().strip()

    replacements = {
        " street": " st",
        " avenue": " ave",
        " boulevard": " blvd",
        " road": " rd",
        " drive": " dr",
        " lane": " ln",
        " highway": " hwy",
        " north": " n",
        " south": " s",
        " east": " e",
        " west": " w",
        " northwest": " nw",
        " northeast": " ne",
        " southwest": " sw",
        " southeast": " se",
    }

    for old, new in replacements.items():
        value = value.replace(old, new)

    value = re.sub(r"[^a-z0-9]", "", value)

    return value


def address_match(community, account):
    """Check whether the website and CRM addresses match."""
    return (
        normalize_address(community.get("street"))
        == normalize_address(account.get("billing_street"))
        and community.get("city", "").lower().strip()
        == account.get("billing_city", "").lower().strip()
        and community.get("state", "").lower().strip()
        == account.get("billing_state", "").lower().strip()
        and community.get("zip", "").strip()
        == account.get("billing_zip", "").strip()
    )


def name_match(community, account):
    """Check whether normalized names match."""
    return normalize_text(community.get("name")) == normalize_text(
        account.get("name")
    )


def find_match(community, accounts):
    """
    Find the best CRM match for a website community.
    Address is the strongest identifier.
    """
    for account in accounts:
        if address_match(community, account):
            if name_match(community, account):
                reason = "Website and CRM name and address match."
            else:
                reason = "Address matches, but the CRM account name differs."

            return {
                "classification": "confident_match",
                "account": account,
                "reason": reason,
            }

    for account in accounts:
        if name_match(community, account):
            return {
                "classification": "match_needing_fix",
                "account": account,
                "reason": "Names match after normalization, but addresses differ.",
            }

    return {
        "classification": "missing_crm_account",
        "account": None,
        "reason": "No matching CRM account was found.",
    }
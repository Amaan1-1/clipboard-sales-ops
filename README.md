# Clipboard Sales Operations Assessment

A CRM data-quality system for reconciling Bellhaven Senior Living facilities with CRM accounts.

## What It Does

- Scrapes Bellhaven facility information
- Matches facilities to CRM accounts
- Identifies missing, outdated, duplicate, or incorrect records
- Provides a review interface for proposed changes
- Applies only approved changes through the CRM API
- Handles billing/CHOW rules
- Supports safe, repeatable daily runs

## Tech Stack

- Python
- BeautifulSoup
- Requests
- SQLite
- GitHub Actions

## Structure

```text
app/
├── scraper.py
├── crm.py
├── matcher.py
├── pipeline.py
└── review_app.py

tests/
data/
.github/
requirements.txt
README.md

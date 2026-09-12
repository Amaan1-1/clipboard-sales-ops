 Bellhaven Sales Ops Data Pipeline & Review App

An automated sales operations and data hygiene pipeline built for Bellhaven Senior Living to reconcile website locations with CRM sandbox accounts, enforce strict billing and Change of Ownership (CHOW) SOPs, and provide a human-gated review interface before updating the CRM API.

## Project Structure

```text
clipboard-sales-ops-assessment/
├── .github/
│   └── workflows/
│       └── schedule.yml
├── .pytest_cache/
├── .venv/
├── app/
│   ├── __pycache__/
│   ├── __init__.py
│   ├── actions.py
│   ├── crm.py
│   ├── database.py
│   ├── export.py
│   ├── matcher.py
│   ├── pipeline.py
│   ├── proposal.py
│   ├── review_app.py
│   └── scraper.py
├── data/
│   ├── .gitkeep
│   └── reviews.db
├── output/
│   ├── recommendations.json
│   └── summary.json
├── tests/
│   ├── __pycache__/
│   └── test_matcher.py
├── .env
├── .gitignore
├── README.md
└── requirements.txt
```

## Core Features

- **Automated Web Scraping (`scraper.py`)**: Extracts live location details, addresses, and care types from the Bellhaven website.
- **Normalization & Matching (`matcher.py`)**: Evaluates and matches scraped data against CRM accounts using address normalization and name matching.
- **CHOW & Billing SOP Compliance (`actions.py`)**: Enforces corporate finance rules where accounts with `lifetime_revenue > 0` AND `outstanding_ar > 0` trigger a Change of Ownership (preserving the historical account and creating a new record under the Bellhaven parent), while others undergo direct re-parenting.
- **Duplicate Management**: Marks duplicate accounts as `Inactive` and populates `duplicate_of_account` pointing to the surviving record ID.
- **Gated Flask Review App (`review_app.py`)**: Displays a local queue of generated proposals with supporting evidence, ensuring all CRM write operations require explicit human approval.
- **Idempotent Execution & Testing**: Fully integrated with SQLite for persistent local tracking and backed by a comprehensive `pytest` suite.

## Getting Started

1. **Install Dependencies:**
   ```cmd
   pip install -r requirements.txt
   ```

2. **Run the Pipeline:**
   Scrapes the website, matches records, and populates the local SQLite queue (`data/reviews.db`):
   ```cmd
   python -m app.pipeline
   ```

3. **Launch the Local Review App:**
   ```cmd
   python -m app.review_app
   ```
   Open `http://127.0.0.1:5000` in your browser to inspect proposals and execute approved updates against the live CRM sandbox API.

4. **Run Tests:**
   ```cmd
   pytest
   ```

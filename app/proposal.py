from app.database import get_connection


def add_proposal(
    proposal_id,
    facility_name,
    action,
    details
):
    conn = get_connection()

    conn.execute(
        """
        INSERT OR IGNORE INTO proposals
        (
            proposal_id,
            facility_name,
            action,
            details
        )
        VALUES (?, ?, ?, ?)
        """,
        (
            proposal_id,
            facility_name,
            action,
            details
        )
    )

    conn.commit()
    conn.close()

if __name__ == "__main__":
    add_proposal(
        "rename_chagrin_falls",
        "Bellhaven of Chagrin Falls",
        "rename_account",
        "Rename Riverbend Manor Care Center to Bellhaven of Chagrin Falls"
    )
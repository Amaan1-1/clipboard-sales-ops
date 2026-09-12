import pytest
from app.matcher import normalize_text, normalize_address, find_match


class TestNormalizeText:
    def test_lowercasing_and_whitespace(self):
        assert normalize_text("  Bellhaven Senior Living  ") == "bellhaven senior living"

    def test_ampersand_conversion(self):
        assert normalize_text("Rehab & Nursing") == normalize_text("Rehab and Nursing")

    def test_cosmetic_synonyms(self):
        # Normalizes variations like 'rehabilitation' -> 'rehab' and 'centre' -> 'center'
        term_a = normalize_text("Bellhaven Rehabilitation Centre")
        term_b = normalize_text("Bellhaven Rehab Center")
        assert term_a == term_b

    def test_punctuation_stripping(self):
        assert normalize_text("Bellhaven, Inc.") == "bellhaven inc"


class TestNormalizeAddress:
    def test_basic_address_cleaning(self):
        addr1 = "100 Main St, Chagrin Falls, OH 44022"
        addr2 = "100 Main St Chagrin Falls OH 44022"
        assert normalize_address(addr1) == normalize_address(addr2)

    def test_case_insensitivity(self):
        addr1 = "118 UNION SQUARE DR NEW ALBANY OH 43054"
        addr2 = "118 union square dr new albany oh 43054"
        assert normalize_address(addr1) == normalize_address(addr2)


class TestFindMatch:
    @pytest.fixture
    def sample_crm_accounts(self):
        return [
            {
                "account_id": "ACC001",
                "name": "Riverbend Manor Care Center",
                "billing_street": "100 Main St",
                "billing_city": "Chagrin Falls",
                "billing_state": "OH",
                "billing_zip": "44022",
                "parent_name": "Cedar Trail Communities (Parent Account)",
                "lifetime_revenue": "1000.00",
                "outstanding_ar": "0.00",
                "care_type": "Assisted Living",
                "status": "Active"
            },
            {
                "account_id": "ACC002",
                "name": "Bellhaven at Union Square",
                "billing_street": "118 Union Square Dr",
                "billing_city": "New Albany",
                "billing_state": "OH",
                "billing_zip": "43054",
                "parent_name": "Bellhaven Senior Living (Parent Account)",
                "lifetime_revenue": "5000.00",
                "outstanding_ar": "100.00",
                "care_type": "Memory Care",
                "status": "Active"
            }
        ]

    def test_exact_address_and_name_match(self, sample_crm_accounts):
        community = {
            "name": "Bellhaven at Union Square",
            "street": "118 Union Square Dr",
            "city": "New Albany",
            "state": "OH",
            "zip": "43054",
            "care_offerings": ["Memory Support"]
        }
        result = find_match(community, sample_crm_accounts)
        assert result["account"] is not None
        assert result["account"]["account_id"] == "ACC002"

    def test_rebrand_match_by_address(self, sample_crm_accounts):
        # Address matches ACC001, but facility name on website has rebranded
        community = {
            "name": "Bellhaven of Chagrin Falls",
            "street": "100 Main St",
            "city": "Chagrin Falls",
            "state": "OH",
            "zip": "44022",
            "care_offerings": ["Assisted Living"]
        }
        result = find_match(community, sample_crm_accounts)
        assert result["account"] is not None
        assert result["account"]["account_id"] == "ACC001"

    def test_missing_crm_account(self, sample_crm_accounts):
        # Community not found in current CRM accounts
        community = {
            "name": "Bellhaven of Batavia",
            "street": "2000 Hospital Dr",
            "city": "Batavia",
            "state": "OH",
            "zip": "45103",
            "care_offerings": ["Assisted Living"]
        }
        result = find_match(community, sample_crm_accounts)
        assert result["classification"] == "missing_crm_account"
        assert result["account"] is None
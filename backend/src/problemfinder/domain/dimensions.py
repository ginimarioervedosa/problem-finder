"""Cross-source analysis dimensions assigned during enrichment.

These enums normalise wildly different source vocabularies into a shared set.
They will evolve; every assignment is recomputable from the raw store, so
extending them is cheap by design.
"""

from enum import StrEnum


class ProductDomain(StrEnum):
    BANKING_AND_CREDIT = "banking_and_credit"
    MORTGAGES_AND_HOME_FINANCE = "mortgages_and_home_finance"
    INSURANCE_AND_PROTECTION = "insurance_and_protection"
    INVESTMENTS = "investments"
    PENSIONS_AND_DECUMULATION = "pensions_and_decumulation"
    WEALTH_MANAGEMENT = "wealth_management"
    TAX = "tax"
    LEGAL_SERVICES = "legal_services"
    FUNERAL_PLANNING = "funeral_planning"
    OTHER = "other"


class WealthSegment(StrEnum):
    BUSINESS_OWNER = "business_owner"
    SENIOR_PROFESSIONAL = "senior_professional"
    INHERITED_WEALTH = "inherited_wealth"
    PROPERTY_INVESTOR = "property_investor"
    RETIREE = "retiree"
    OTHER = "other"

"""The shipped taxonomy file stays valid and covers every known source category."""

from pathlib import Path

from problemfinder.enrichment.taxonomy import load_taxonomy

TAXONOMY_PATH = Path(__file__).parents[2] / "config" / "taxonomy.yaml"

# The category vocabulary each source actually emits, checked against the map
# so a taxonomy edit can never silently orphan a known label.
FOS_COMPLAINTS_CATEGORIES = (
    "Banking & Credit",
    "Decumulation Life & Pensions",
    "Funeral Planning Services",
    "General Insurance / Pure Protection",
    "Investments",
    "Mortgages & Home Finance",
    "PPI",
)
FOS_DECISIONS_CATEGORIES = (
    "Banking and Payments",
    "Consumer Credit",
    "Insurance",
    "Pensions and Annuities",
    "Mortgages",
    "Investments",
    "Funeral Planning Services",
    "Claims Management",
)


def test_shipped_taxonomy_parses_and_validates() -> None:
    taxonomy = load_taxonomy(TAXONOMY_PATH)
    assert taxonomy.themes


def test_every_known_source_category_maps_to_a_product_domain() -> None:
    mapped = set(load_taxonomy(TAXONOMY_PATH).product_domains)
    assert set(FOS_COMPLAINTS_CATEGORIES) <= mapped
    assert set(FOS_DECISIONS_CATEGORIES) <= mapped


def test_theme_names_are_unique() -> None:
    names = [theme.name for theme in load_taxonomy(TAXONOMY_PATH).themes]
    assert len(names) == len(set(names))

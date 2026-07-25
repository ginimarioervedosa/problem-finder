"""The theme taxonomy: configuration, not code, because opinions drift.

`backend/config/taxonomy.yaml` declares the themes, their keyword rules, and
the source-category to product-domain map. Passes receive a loaded Taxonomy;
only this module touches the file.
"""

from pathlib import Path

import yaml
from pydantic import BaseModel, ConfigDict, Field

from problemfinder.domain.dimensions import ProductDomain


class SubTheme(BaseModel):
    model_config = ConfigDict(frozen=True)

    name: str
    keywords: tuple[str, ...] = Field(min_length=1)


class Theme(BaseModel):
    model_config = ConfigDict(frozen=True)

    name: str
    keywords: tuple[str, ...] = Field(min_length=1)
    sub_themes: tuple[SubTheme, ...] = ()


class Taxonomy(BaseModel):
    """Declaration order of `themes` is the tie-break priority when scoring."""

    model_config = ConfigDict(frozen=True)

    product_domains: dict[str, ProductDomain]
    themes: tuple[Theme, ...]


def load_taxonomy(path: Path) -> Taxonomy:
    return Taxonomy.model_validate(yaml.safe_load(path.read_text(encoding="utf-8")))

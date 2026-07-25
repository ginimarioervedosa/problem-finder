"""Resolution base for a page's relative hrefs, honouring any <base> tag.

FOS pages carry a <base href> pointing at the site root, so relative hrefs
must resolve against it rather than against the page's own URL. Shared by
every adapter that walks the FOS site; never copied between adapters.
"""

import httpx
from selectolax.parser import HTMLParser


def page_base(tree: HTMLParser, page_url: str) -> httpx.URL:
    base = tree.css_first("base")
    return httpx.URL((base.attributes.get("href") if base else None) or page_url)

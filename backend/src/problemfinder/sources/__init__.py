"""Sources layer: one adapter package per data source, behind one protocol.

Everything the rest of the codebase knows about a source is the `Source`
protocol and its `SourcePolicy`. Fetching and parsing libraries (httpx,
selectolax, Playwright) exist only below this package; import-linter enforces
that, and enforces that adapters never import each other.
"""

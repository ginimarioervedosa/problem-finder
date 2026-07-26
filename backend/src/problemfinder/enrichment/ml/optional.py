"""The one error a missing ml extras install produces, with its remedy."""


class MlExtrasMissingError(RuntimeError):
    """An ml-extras package was needed but is not installed."""

    def __init__(self, package: str) -> None:
        super().__init__(
            f"{package} is not installed; run `uv sync --extra ml` in backend/ "
            "to enable ML enrichment"
        )

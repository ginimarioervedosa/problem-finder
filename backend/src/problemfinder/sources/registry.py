"""Adapter registry: the pipeline discovers sources here, never by import.

Adapters self-register with the @register decorator; load_adapters() imports
every module under sources.adapters so registration is a side effect of the
package existing. Adding a source therefore never edits core code.
"""

import importlib
import pkgutil
from collections.abc import Mapping

from problemfinder.sources import adapters
from problemfinder.sources.protocol import Source


class UnknownSourceError(LookupError):
    """Raised when a source key has no registered adapter."""


_registry: dict[str, Source] = {}


def register[S: type[Source]](source_cls: S) -> S:
    """Class decorator: instantiate the adapter and index it by its key."""
    instance = source_cls()
    _registry[instance.key] = instance
    return source_cls


def get(key: str) -> Source:
    load_adapters()
    if key not in _registry:
        known = ", ".join(sorted(_registry)) or "none registered"
        raise UnknownSourceError(f"no source adapter for key {key!r} (known: {known})")
    return _registry[key]


def all_sources() -> Mapping[str, Source]:
    load_adapters()
    return dict(_registry)


def load_adapters() -> None:
    """Import every adapter package so @register has run for each of them."""
    for module in pkgutil.walk_packages(adapters.__path__, prefix=f"{adapters.__name__}."):
        importlib.import_module(module.name)

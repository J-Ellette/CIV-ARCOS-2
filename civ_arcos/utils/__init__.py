"""Utility functions for CIV-ARCOS."""
import os
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, Iterator, Optional

from civ_arcos.evidence.collector import Evidence


def make_evidence(
    ev_type: str,
    source: str,
    data: Dict[str, Any],
    provenance: Optional[Dict[str, Any]] = None,
) -> Evidence:
    """Create an :class:`Evidence` instance with a generated id and timestamp.

    Parameters
    ----------
    ev_type:
        The evidence type string (e.g. ``"static_analysis"``).
    source:
        The originating source path or URL.
    data:
        The payload dictionary.
    provenance:
        Optional provenance metadata.  When *None* a default dict of
        ``{"collector": ev_type, "source_path": source}`` is used.
    """
    return Evidence(
        id=str(uuid.uuid4()),
        type=ev_type,
        source=source,
        timestamp=datetime.now(timezone.utc).isoformat(),
        data=data,
        provenance=provenance if provenance is not None else {"collector": ev_type, "source_path": source},
    )


def iter_python_files(path: str) -> Iterator[str]:
    """Yield absolute paths of every ``*.py`` file found under *path*.

    If *path* is a regular file it is yielded directly (when it ends with
    ``.py``).  Otherwise the directory tree rooted at *path* is walked.
    """
    if os.path.isfile(path):
        if path.endswith(".py"):
            yield path
        return
    for root, _dirs, files in os.walk(path):
        for fname in files:
            if fname.endswith(".py"):
                yield os.path.join(root, fname)

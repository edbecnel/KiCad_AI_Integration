"""wx-aware type aliases safe in KiCad's embedded Python 3.9 runtime.

KiCad ships Python 3.9.x with wx types implemented as SIP wrapper classes.
PEP 604 unions (``X | Y``) are evaluated at runtime inside ``Callable[...]``
subscripts and similar assignments, which breaks for wx types::

    Callable[[Path, wx.Window | None], None]  # TypeError on import in KiCad

Use ``Optional[wx.Window]`` (or ``Union[...]``) in those positions instead.
Function parameter annotations are fine with ``from __future__ import annotations``.
"""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path
from typing import Optional

try:
    import wx
except ImportError:  # pragma: no cover
    wx = None  # type: ignore[assignment]

ModalOpener = Callable[[Path, Optional[wx.Window]], None]

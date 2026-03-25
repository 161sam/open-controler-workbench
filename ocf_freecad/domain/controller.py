from __future__ import annotations

from copy import deepcopy
from typing import Any


class Controller:
    def __init__(
        self,
        id,
        width,
        depth,
        height,
        top_thickness,
        surface: dict[str, Any] | None = None,
    ):
        self.id = id
        self.width = width
        self.depth = depth
        self.height = height
        self.top_thickness = top_thickness
        self.surface = deepcopy(surface) if surface is not None else None

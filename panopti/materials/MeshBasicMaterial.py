from dataclasses import dataclass
from typing import List, Optional, Union
from .base import BaseMaterial


@dataclass
class MeshBasicMaterial(BaseMaterial):
    """Simple material that renders without lighting - shows raw colors.
    See: https://threejs.org/docs/#api/en/materials/MeshBasicMaterial
    """
    def to_dict(self) -> dict:
        """Convert to dictionary for serialization."""
        return super().to_dict() 
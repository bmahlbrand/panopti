from dataclasses import dataclass
from typing import List, Optional, Union
from .base import BaseMaterial


@dataclass
class MeshNormalMaterial(BaseMaterial):
    """Material for visualizing normal vectors - useful for debugging. See: [https://threejs.org/docs/#api/en/materials/MeshNormalMaterial](https://threejs.org/docs/#api/en/materials/MeshNormalMaterial)
    """
    
    def __post_init__(self):
        """Initialize with defaults and validate."""
        super().__post_init__()
        
    def to_dict(self) -> dict:
        """Convert to dictionary for serialization."""
        base_dict = super().to_dict()
        return base_dict 
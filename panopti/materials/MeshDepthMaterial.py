from dataclasses import dataclass
from typing import List, Optional, Union
from .base import BaseMaterial


@dataclass
class MeshDepthMaterial(BaseMaterial):
    """Material for depth-based rendering - renders depth as grayscale. For details on the parameters listed below,
    refer to: [https://threejs.org/docs/#api/en/materials/MeshDepthMaterial](https://threejs.org/docs/#api/en/materials/MeshDepthMaterial)

    Supported parameters:
    ```
    - depth_packing: str, "basic" or "rgba"
    ```
    """
    
    depth_packing: str = "basic"  # "basic" or "rgba"
    
    def __post_init__(self):
        """Initialize with defaults and validate."""
        super().__post_init__()
    
    def to_dict(self) -> dict:
        """Convert to dictionary for serialization."""
        base_dict = super().to_dict()
        base_dict.update({
            'depth_packing': self.depth_packing,
        })
        return base_dict 
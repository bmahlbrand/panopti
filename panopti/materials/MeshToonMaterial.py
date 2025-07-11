from dataclasses import dataclass, field
from typing import List, Optional, Union
from .base import BaseMaterial
import numpy as np

def _convert_scalar(val):
    """Convert numpy scalar to Python scalar."""
    return val.item() if isinstance(val, np.generic) else val

@dataclass
class MeshToonMaterial(BaseMaterial):
    """Material for cel-shaded rendering. For details on the parameters listed below,
    refer to: [https://threejs.org/docs/#api/en/materials/MeshToonMaterial](https://threejs.org/docs/#api/en/materials/MeshToonMaterial)

    Supported parameters:
    ```
    - emissive: RGB array [r,g,b] or hex string
    - emissive_intensity: float between 0 and 1
    ```
    """
    
    emissive: Union[List[float], str] = field(default=None)
    emissive_intensity: float = field(default=1.0)

    def __post_init__(self):
        """Initialize with defaults and validate."""
        super().__post_init__()
        
        if self.emissive is None:
            self.emissive = [0.0, 0.0, 0.0]
    
    def to_dict(self) -> dict:
        """Convert to dictionary for serialization."""
        base_dict = super().to_dict()
        base_dict.update({
            'emissive': self.emissive,
            'emissive_intensity': self.emissive_intensity,
        })
        return base_dict 
from dataclasses import dataclass, field
from typing import List, Optional, Union
import numpy as np

def _convert_scalar(val):
    """Convert numpy scalar to Python scalar."""
    return val.item() if isinstance(val, np.generic) else val

@dataclass
class BaseMaterial:
    """Base class for all materials types with common properties. For details on the parameters listed below,
    refer to: [https://threejs.org/docs/#api/en/materials/Material](https://threejs.org/docs/#api/en/materials/Material)

    Supported parameters:
    ```
    - flat_shading: bool
    - color: RGB array [r,g,b] or hex string
    - opacity: float between 0 and 1
    - transparent: bool
    - alpha_test: float between 0 and 1
    - side: str, "front", "back", "double"
    - wireframe: bool
    - wireframe_linewidth: float
    - depth_test: bool
    - depth_write: bool
    - tone_mapped: bool
    ```
    """
    
    flat_shading: bool = field(default=False)
    color: Union[List[float], str] = field(default=None)
    opacity: float = field(default=1.0)
    transparent: bool = field(default=False)
    alpha_test: float = field(default=0.0)
    side: str = field(default="front")
    wireframe: bool = field(default=False)
    wireframe_linewidth: float = field(default=1.0)
    depth_test: bool = field(default=True)
    depth_write: bool = field(default=True)
    tone_mapped: bool = field(default=True)

    def __setattr__(self, name, value):
        """Convert numpy scalars to Python scalars when setting attributes."""
        super().__setattr__(name, _convert_scalar(value))
    
    def __post_init__(self):
        """Validate and set default color if not provided."""
        if self.color is None:
            self.color = [1.0, 1.0, 1.0]  # Default white
        
        if self.opacity < 1.0:
            self.transparent = True
    
    def to_dict(self) -> dict:
        """Convert material to dictionary for serialization."""
        return {
            'type': self.__class__.__name__,
            'color': self.color,
            'opacity': self.opacity,
            'transparent': self.transparent,
            'alpha_test': self.alpha_test,
            'side': self.side,
            'wireframe': self.wireframe,
            'wireframe_linewidth': self.wireframe_linewidth,
            'depth_test': self.depth_test,
            'depth_write': self.depth_write,
            'tone_mapped': self.tone_mapped
        }

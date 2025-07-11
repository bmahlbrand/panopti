from dataclasses import dataclass, field
from typing import List, Optional, Union
from .base import BaseMaterial
import numpy as np

def _convert_scalar(val):
    """Convert numpy scalar to Python scalar."""
    return val.item() if isinstance(val, np.generic) else val

@dataclass
class MeshPhysicalMaterial(BaseMaterial):
    """Extended physically-based material with additional properties for realistic rendering. For details on the parameters listed below,
    refer to: [https://threejs.org/docs/#api/en/materials/MeshPhysicalMaterial](https://threejs.org/docs/#api/en/materials/MeshPhysicalMaterial)

    Supported parameters:
    ```
    - roughness
    - metalness
    - emissive
    - emissive_intensity
    - reflectivity
    - sheen
    - sheen_roughness
    - sheen_color
    - specular_intensity
    - specular_color
    - ior
    - anisotropy
    - anisotropy_rotation
    - iridescence
    - iridescence_ior
    - iridescence_thickness_range
    - clearcoat
    - clearcoat_roughness
    - transmission
    - thickness
    - attenuation_distance
    - attenuation_color
    ```
    """
    
    roughness: float = field(default=0.5)
    metalness: float = field(default=0.0)
    
    emissive: Union[List[float], str] = field(default=None)
    emissive_intensity: float = field(default=1.0)
    
    reflectivity: float = field(default=0.5)
    
    sheen: float = field(default=0.0)
    sheen_roughness: float = field(default=1.0)
    sheen_color: Union[List[float], str] = field(default=None)
    
    specular_intensity: float = field(default=1.0)
    specular_color: Union[List[float], str] = field(default=None)
    
    ior: float = field(default=1.5)

    anisotropy: float = field(default=0.0)
    anisotropy_rotation: float = field(default=0.0)
    
    iridescence: float = field(default=0.0)
    iridescence_ior: float = field(default=1.3)
    iridescence_thickness_range: List[float] = field(default=None)
    
    clearcoat: float = field(default=0.0)
    clearcoat_roughness: float = field(default=0.0)

    transmission: float = field(default=0.0)
    thickness: float = field(default=0.0)

    attenuation_distance: float = field(default=1.0)
    attenuation_color: Union[List[float], str] = field(default=None)
    
    def __post_init__(self):
        """Initialize with defaults and validate."""
        super().__post_init__()
        
        if self.emissive is None:
            self.emissive = [0.0, 0.0, 0.0]
        
        if self.sheen_color is None:
            self.sheen_color = [1.0, 1.0, 1.0]
        
        if self.specular_color is None:
            self.specular_color = [1.0, 1.0, 1.0]
        
        if self.iridescence_thickness_range is None:
            self.iridescence_thickness_range = [100.0, 400.0]
        
        if self.attenuation_color is None:
            self.attenuation_color = [1.0, 1.0, 1.0]
    
    def to_dict(self) -> dict:
        """Convert to dictionary for serialization."""
        base_dict = super().to_dict()
        base_dict.update({
            'roughness': self.roughness,
            'metalness': self.metalness,
            'flat_shading': self.flat_shading,
            'emissive': self.emissive,
            'emissive_intensity': self.emissive_intensity,
            'reflectivity': self.reflectivity,
            'sheen': self.sheen,
            'sheen_roughness': self.sheen_roughness,
            'sheen_color': self.sheen_color,
            'specular_intensity': self.specular_intensity,
            'specular_color': self.specular_color,
            'anisotropy': self.anisotropy,
            'anisotropy_rotation': self.anisotropy_rotation,
            'iridescence': self.iridescence,
            'iridescence_ior': self.iridescence_ior,
            'iridescence_thickness_range': self.iridescence_thickness_range,
            'clearcoat': self.clearcoat,
            'clearcoat_roughness': self.clearcoat_roughness,
            'transmission': self.transmission,
            'thickness': self.thickness,
            'attenuation_distance': self.attenuation_distance,
            'attenuation_color': self.attenuation_color,
            'ior': self.ior
        })
        return base_dict 
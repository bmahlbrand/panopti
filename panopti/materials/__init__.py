"""
Material system for Panopti viewer.

This module provides dataclasses for defining materials that can be applied to
Mesh and AnimatedMesh objects. The materials support a subset of Three.js 
material features that are most useful for scientific visualization and debugging.
"""

from .base import BaseMaterial
from .MeshStandardMaterial import MeshStandardMaterial
from .MeshPhysicalMaterial import MeshPhysicalMaterial
from .MeshBasicMaterial import MeshBasicMaterial
from .MeshToonMaterial import MeshToonMaterial
from .MeshNormalMaterial import MeshNormalMaterial
from .MeshDepthMaterial import MeshDepthMaterial
from .utils import create_material_from_dict

# Material presets:
class _MaterialPresets:
    
    @property
    def default(self) -> MeshStandardMaterial:
        return self.plastic

    @property
    def plastic(self) -> MeshStandardMaterial:
        return MeshStandardMaterial()
    
    @property
    def glossy(self) -> MeshStandardMaterial:
        return MeshStandardMaterial(
            roughness=0.0,
            metalness=0.0,
        )
    
    @property
    def metal(self) -> MeshPhysicalMaterial:
        return MeshPhysicalMaterial(
            roughness=0.0,
            metalness=0.6,
            clearcoat=0.30,
        )
    
    @property
    def flat(self) -> MeshBasicMaterial:
        return MeshBasicMaterial(
            flat_shading=True,
        )
    
    @property
    def chalk(self) -> MeshStandardMaterial:
        return MeshStandardMaterial(
            roughness=1.0,
            metalness=0.0,
        )
    
    @property
    def normals(self) -> MeshNormalMaterial:
        return MeshNormalMaterial()

    @property
    def marble(self):
        return MeshPhysicalMaterial(
            roughness=0.35,
            metalness=0.0,
            clearcoat=0.30,
            clearcoat_roughness=0.20,
            transmission=0.30,
            thickness=2.0,
            specular_intensity=1.0,
            specular_color='#004d40',
        )

MaterialPresets = _MaterialPresets()

__all__ = [
    'BaseMaterial',
    'MeshStandardMaterial',
    'MeshPhysicalMaterial', 
    'MeshBasicMaterial',
    'MeshToonMaterial',
    'MeshNormalMaterial',
    'MeshDepthMaterial',
    'MaterialPresets',
    'create_material_from_dict',
]

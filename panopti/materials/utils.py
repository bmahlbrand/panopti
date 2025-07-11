from typing import Dict, Any, Union, List
from .base import BaseMaterial
from .MeshStandardMaterial import MeshStandardMaterial
from .MeshPhysicalMaterial import MeshPhysicalMaterial
from .MeshBasicMaterial import MeshBasicMaterial
from .MeshToonMaterial import MeshToonMaterial
from .MeshNormalMaterial import MeshNormalMaterial
from .MeshDepthMaterial import MeshDepthMaterial

def create_material_from_dict(material_dict: Dict[str, Any]) -> BaseMaterial:
    """
    Create a material instance from a dictionary.
    
    Args:
        material_dict: Dictionary containing material data with 'type' field
        
    Returns:
        Material instance of the appropriate type
        
    Raises:
        ValueError: If material type is not supported
    """
    material_type = material_dict.get('type')
    
    if material_type == 'MeshStandardMaterial':
        return MeshStandardMaterial(**{k: v for k, v in material_dict.items() if k != 'type'})
    elif material_type == 'MeshPhysicalMaterial':
        return MeshPhysicalMaterial(**{k: v for k, v in material_dict.items() if k != 'type'})
    elif material_type == 'MeshBasicMaterial':
        return MeshBasicMaterial(**{k: v for k, v in material_dict.items() if k != 'type'})
    elif material_type == 'MeshToonMaterial':
        return MeshToonMaterial(**{k: v for k, v in material_dict.items() if k != 'type'})
    elif material_type == 'MeshNormalMaterial':
        return MeshNormalMaterial(**{k: v for k, v in material_dict.items() if k != 'type'})
    elif material_type == 'MeshDepthMaterial':
        return MeshDepthMaterial(**{k: v for k, v in material_dict.items() if k != 'type'})
    else:
        raise ValueError(f"Unsupported material type: {material_type}")

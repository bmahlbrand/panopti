
from .mesh import Mesh
from .animated_mesh import AnimatedMesh
from .points import Points
from .arrows import Arrows
import inspect

object_map = {
    "mesh": Mesh,
    "animated_mesh": AnimatedMesh,
    "points": Points,
    "arrows": Arrows,
}

def clean_kwargs_dict(cls, data: dict):
    sig = inspect.signature(cls)
    keep = {k: v for k, v in data.items() if k in sig.parameters}
    return keep

def export_object_from_dict(obj_dict: dict) -> bytes:
    """Export an object from its dictionary representation."""
    # TODO revisit this mess
    obj_type = obj_dict.get("type")
    obj_class = object_map.get(obj_type)
    if not obj_class:
        raise ValueError(f"Unknown object type: {obj_type}")
    
    # Leading None is for "viewer" positional argument
    obj = obj_class(None, **clean_kwargs_dict(obj_class, obj_dict))
    if hasattr(obj, 'export'):
        return obj.export()
    else:
        raise ValueError(f"Object of type {obj_type} does not support export.")
# panopti/objects/arrows.py
from typing import Dict, Any, Union, Tuple, List
import numpy as np

from .base import SceneObject

class Arrows(SceneObject):
    def __init__(self, viewer, starts, ends, name: str,
                color: Union[Tuple[float, float, float], List[Tuple[float, float, float]]] = (0, 0, 0),
                width: float = 1.0, opacity: float = 1.0, visible: bool = True):
        super().__init__(viewer, name)
        
        self._check_for_nans(
            starts=starts,
            ends=ends,
            color=color,
            width=width,
            opacity=opacity,
        )

        self.starts = self._convert_to_list(starts)
        self.ends = self._convert_to_list(ends)
        self.color = self._convert_to_list(color)
        self.width = width
        self.visible = visible
        self.opacity = opacity
    
    def _convert_to_list(self, data):
        if isinstance(data, np.ndarray):
            return data.tolist()
        return data
    
    def to_dict(self) -> Dict[str, Any]:
        data = {
            "id": self.name,
            "name": self.name,
            "type": "arrows",
            "starts": self.starts,
            "ends": self.ends,
            "color": self.color,
            "width": self.width,
            "visible": self.visible,
            "opacity": self.opacity,
            "warnings": self.warnings,
        }
        return self._sanitize_for_json(data)

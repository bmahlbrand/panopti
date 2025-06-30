# panopti/objects/points.py
import io
import numpy as np

from typing import Dict, Any, Optional, Tuple, List, Union
from .base import SceneObject

class Points(SceneObject):
    def __init__(self, viewer, points, name: str,
                colors: Union[Tuple[float, float, float], List[Tuple[float, float, float]]] = (0.5, 0.5, 0.5),
                size: float = 0.01, visible: bool = True,
                opacity: float = 1.0):
        super().__init__(viewer, name)
        
        self._check_for_nans(
            points=points,
            colors=colors,
            size=size,
            opacity=opacity,
        )

        self.points = self._convert_to_list(points)
        self.colors = self._convert_to_list(colors)
        self.size = size
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
            "type": "points",
            "points": self.points,
            "colors": self.colors,
            "size": self.size,
            "visible": self.visible,
            "opacity": self.opacity,
            "warnings": self.warnings,
        }
        return self._sanitize_for_json(data)
    
    def export(self) -> bytes:
        """Export the points as numpy array."""
        points = np.array(self.points)
        buffer = io.BytesIO()
        np.savez(buffer, points=self.points, colors=self.colors)
        buffer.seek(0)
        return buffer.getvalue()

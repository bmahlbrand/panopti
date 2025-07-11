# panopti/objects/points.py
import io
import numpy as np

from typing import Dict, Any, Optional, Tuple, List, Union
from .base import SceneObject

class Points(SceneObject):
    def __init__(self, 
                 viewer, 
                 points, 
                 name: str,
                 colors: Union[Tuple[float, float, float], List[Tuple[float, float, float]], np.ndarray] = (0.5, 0.5, 0.5),
                 size: float = 0.01, 
                 visible: bool = True,
                 opacity: float = 1.0,
                 position: Union[Tuple[float, float, float], np.ndarray] = (0, 0, 0),
                 rotation: Union[Tuple[float, float, float], np.ndarray] = (0, 0, 0),
                 scale: Union[Tuple[float, float, float], np.ndarray] = (1.0, 1.0, 1.0)):
        super().__init__(viewer, name)
        
        self._check_for_nans(
            points=points,
            colors=colors,
            size=size,
            opacity=opacity,
            position=position,
            rotation=rotation,
            scale=scale,
        )

        self.points = np.asarray(points, dtype=np.float32)
        self.colors = np.asarray(colors, dtype=np.float32)
        self.size = size
        self.visible = visible
        self.opacity = opacity
        self.position = np.asarray(position, dtype=np.float32)
        self.rotation = np.asarray(rotation, dtype=np.float32)
        self.scale = np.asarray(scale, dtype=np.float32)

    
    def to_dict(self, serialize: bool = True) -> Dict[str, Any]:
        data = {
            "id": self.name,
            "name": self.name,
            "type": "points",
            "points": self.points,
            "colors": self.colors,
            "size": self.size,
            "visible": self.visible,
            "opacity": self.opacity,
            "position": self.position,
            "rotation": self.rotation,
            "scale": self.scale,
            "warnings": self.warnings,
        }
        return self._to_serializable(data) if serialize else data
    
    @property
    def trans_mat(self) -> np.ndarray:
        """Returns the 4x4 transformation matrix corresponding to 
        the object's position, rotation, and scale in the viewer."""
        tx, ty, tz = self.position.astype(np.float32)
        rx, ry, rz = self.rotation.astype(np.float32)
        sx, sy, sz = self.scale.astype(np.float32)

        cx, sx_ = np.cos(rx), np.sin(rx)
        cy, sy_ = np.cos(ry), np.sin(ry)
        cz, sz_ = np.cos(rz), np.sin(rz)

        Rx = np.array([[1, 0, 0, 0],
                       [0, cx, -sx_, 0],
                       [0, sx_, cx, 0],
                       [0, 0, 0, 1]])
        Ry = np.array([[cy, 0, sy_, 0],
                       [0, 1, 0, 0],
                       [-sy_, 0, cy, 0],
                       [0, 0, 0, 1]])
        Rz = np.array([[cz, -sz_, 0, 0],
                       [sz_, cz, 0, 0],
                       [0, 0, 1, 0],
                       [0, 0, 0, 1]])

        S = np.diag([sx, sy, sz, 1])
        T = np.array([[1, 0, 0, tx],
                      [0, 1, 0, ty],
                      [0, 0, 1, tz],
                      [0, 0, 0, 1]])

        return T @ Rz @ Ry @ Rx @ S

    @property
    def viewer_points(self) -> np.ndarray:
        """Returns the Points' positions under the transformation given by `trans_mat`."""
        points = self.points
        ones = np.ones((points.shape[0], 1))
        hom = np.concatenate([points, ones], axis=1)
        transformed = (self.trans_mat @ hom.T).T
        return transformed[:, :3]
    
    def export(self) -> bytes:
        """Export the points as numpy array."""
        points = self.points
        buffer = io.BytesIO()
        np.savez(buffer, points=self.points, colors=self.colors)
        buffer.seek(0)
        return buffer.getvalue()

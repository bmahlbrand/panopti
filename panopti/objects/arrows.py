# panopti/objects/arrows.py
from typing import Dict, Any, Union, Tuple, List
import numpy as np

from .base import SceneObject

class Arrows(SceneObject):
    def __init__(self, 
                viewer,
                starts,
                ends, 
                name: str,
                color: Union[Tuple[float, float, float], List[Tuple[float, float, float]], np.ndarray] = (0, 0, 0),
                width: float = 0.01, 
                opacity: float = 1.0, 
                visible: bool = True,
                position: Union[Tuple[float, float, float], np.ndarray] = (0, 0, 0),
                rotation: Union[Tuple[float, float, float], np.ndarray] = (0, 0, 0),
                scale: Union[Tuple[float, float, float], np.ndarray] = (1.0, 1.0, 1.0)):
        super().__init__(viewer, name)
        
        self._check_for_nans(
            starts=starts,
            ends=ends,
            color=color,
            width=width,
            opacity=opacity,
            position=position,
            rotation=rotation,
            scale=scale,
        )

        self.starts = np.asarray(starts, dtype=np.float32)
        self.ends = np.asarray(ends, dtype=np.float32)
        self.color = np.asarray(color, dtype=np.float32)
        self.width = width
        self.visible = visible
        self.opacity = opacity
        self.position = np.asarray(position, dtype=np.float32)
        self.rotation = np.asarray(rotation, dtype=np.float32)
        self.scale = np.asarray(scale, dtype=np.float32)
    
    
    def to_dict(self, serialize: bool = True) -> Dict[str, Any]:
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
    def viewer_starts(self) -> np.ndarray:
        """Returns the Arrows' start positions under the transformation given by `trans_mat`."""
        starts = self.starts
        ones = np.ones((starts.shape[0], 1))
        hom = np.concatenate([starts, ones], axis=1)
        transformed = (self.trans_mat @ hom.T).T
        return transformed[:, :3]

    @property
    def viewer_ends(self) -> np.ndarray:
        """Returns the Arrows' end positions under the transformation given by `trans_mat`."""
        ends = self.ends
        ones = np.ones((ends.shape[0], 1))
        hom = np.concatenate([ends, ones], axis=1)
        transformed = (self.trans_mat @ hom.T).T
        return transformed[:, :3]

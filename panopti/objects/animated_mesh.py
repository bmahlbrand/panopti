# panopti/objects/animated_mesh.py
import io
import numpy as np

from typing import Dict, Any, Optional, Tuple, List
from .base import SceneObject

class AnimatedMesh(SceneObject):
    def __init__(self, viewer, vertices, faces, name: str, framerate: float = 24.0,
                wireframe: bool = False, visible: bool = True,
                opacity: float = 1.0,
                position: Tuple[float, float, float] = (0, 0, 0),
                rotation: Tuple[float, float, float] = (0, 0, 0),
                scale: Tuple[float, float, float] = (1, 1, 1),
                color: Tuple[float, float, float] = (0.5, 0.5, 0.5),
                vertex_colors: Optional[List[Tuple[float, float, float]]] = None,
                face_colors: Optional[List[Tuple[float, float, float]]] = None):
        super().__init__(viewer, name)
        
        self._check_for_nans(
            vertices=vertices,
            faces=faces,
            vertex_colors=vertex_colors,
            face_colors=face_colors,
            color=color,
            position=position,
            rotation=rotation,
            scale=scale,
            framerate=framerate,
        )

        # Convert vertices to proper format and validate dimensions
        self.vertices = self._convert_to_list(vertices)
        if len(np.array(self.vertices).shape) != 3:
            raise ValueError("AnimatedMesh vertices must be 3D array with shape (frames, num_vertices, 3)")
        
        self.faces = self._convert_to_list(faces)
        self.framerate = framerate
        self.wireframe = wireframe
        self.visible = visible
        self.opacity = opacity
        self.position = position
        self.rotation = rotation
        self.scale = scale
        self.color = color
        self.vertex_colors = self._convert_to_list(vertex_colors) if vertex_colors is not None else None
        self.face_colors = self._convert_to_list(face_colors) if face_colors is not None else None

        # Animation state
        self.current_frame = 0
        self.num_frames = len(self.vertices)
        self.is_playing = False
        self.start_time = None

        self._check_for_nans(
            vertices=self.vertices,
            faces=self.faces,
            vertex_colors=self.vertex_colors,
            face_colors=self.face_colors,
            color=self.color,
            position=self.position,
            rotation=self.rotation,
            scale=self.scale,
            framerate=self.framerate
        )
    
    def _convert_to_list(self, data):
        if isinstance(data, np.ndarray):
            return data.tolist()
        return data
    
    def to_dict(self) -> Dict[str, Any]:
        data = {
            "id": self.name,
            "name": self.name,
            "type": "animated_mesh",
            "vertices": self.vertices,
            "faces": self.faces,
            "framerate": self.framerate,
            "wireframe": self.wireframe,
            "visible": self.visible,
            "opacity": self.opacity,
            "position": self.position,
            "rotation": self.rotation,
            "scale": self.scale,
            "color": self.color,
            "vertex_colors": self.vertex_colors,
            "face_colors": self.face_colors,
            "current_frame": self.current_frame,
            "num_frames": self.num_frames,
            "is_playing": self.is_playing,
            "warnings": self.warnings,
        }
        return self._sanitize_for_json(data)
    
    def play(self):
        """Start playing the animation"""
        self.is_playing = True
        import time
        self.start_time = time.time()
        
        # Emit update to client
        self.update(is_playing=True, start_time=self.start_time)
    
    def pause(self):
        """Pause the animation"""
        self.is_playing = False
        self.start_time = None
        
        # Emit update to client
        self.update(is_playing=False, start_time=None)
    
    def set_frame(self, frame_index: int):
        """Set to specific frame"""
        if 0 <= frame_index < self.num_frames:
            self.current_frame = frame_index
            self.update(current_frame=frame_index)
    
    def export(self) -> bytes:
        """Export animated mesh to NPZ format with vertices and faces."""        
        vertices = np.array(self.vertices)
        faces = np.array(self.faces)
        buffer = io.BytesIO()
        np.savez_compressed(buffer, vertices=vertices, faces=faces)
        buffer.seek(0)
        return buffer.getvalue()

    @property
    def trans_mat(self) -> np.ndarray:
        tx, ty, tz = self.position
        rx, ry, rz = self.rotation
        sx, sy, sz = self.scale

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
    def viewer_verts(self) -> np.ndarray:
        verts = np.array(self.vertices[self.current_frame])
        ones = np.ones((verts.shape[0], 1))
        hom = np.concatenate([verts, ones], axis=1)
        transformed = (self.trans_mat @ hom.T).T
        return transformed[:, :3]

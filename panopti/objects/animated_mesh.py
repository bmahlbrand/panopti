# panopti/objects/animated_mesh.py
import io
import numpy as np

from typing import Dict, Any, Optional, Tuple, List, Union
from .base import SceneObject

class AnimatedMesh(SceneObject):
    def __init__(self, 
                viewer, 
                vertices, 
                faces, 
                name: str, 
                framerate: float = 24.0,
                visible: bool = True,
                position: Union[Tuple[float, float, float], np.ndarray] = (0, 0, 0),
                rotation: Union[Tuple[float, float, float], np.ndarray] = (0, 0, 0),
                scale: Union[Tuple[float, float, float], np.ndarray] = (1.0, 1.0, 1.0),
                color: Union[Tuple[float, float, float], np.ndarray] = (1.0, 1.0, 1.0),
                vertex_colors: Optional[Union[List[Tuple[float, float, float]], np.ndarray]] = None,
                face_colors: Optional[Union[List[Tuple[float, float, float]], np.ndarray]] = None,
                material: Optional[Any] = None):
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

        self.vertices = np.asarray(vertices, dtype=np.float32)
        if len(self.vertices.shape) != 3:
            raise ValueError("AnimatedMesh vertices must be 3D array with shape (frames, num_vertices, 3)")
        
        self.faces = np.asarray(faces, dtype=np.int32)
        self.framerate = framerate
        self.visible = visible
        self.position = np.asarray(position, dtype=np.float32)
        self.rotation = np.asarray(rotation, dtype=np.float32)
        self.scale = np.asarray(scale, dtype=np.float32)
        self.color = np.asarray(color, dtype=np.float32)
        self.vertex_colors = np.asarray(vertex_colors, dtype=np.float32) if vertex_colors is not None else None
        self.face_colors = np.asarray(face_colors, dtype=np.float32) if face_colors is not None else None
        
        # Store material if provided
        self.material = material

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
    
    
    def to_dict(self, serialize: bool = True) -> Dict[str, Any]:
        data = {
            "id": self.name,
            "name": self.name,
            "type": "animated_mesh",
            "vertices": self.vertices,
            "faces": self.faces,
            "framerate": self.framerate,
            "visible": self.visible,
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
        
        # Add material data if present
        if self.material is not None:
            data["material"] = self.material.to_dict()
        
        return self._to_serializable(data) if serialize else data
    
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
        vertices = self.vertices
        faces = self.faces
        buffer = io.BytesIO()
        np.savez_compressed(buffer, vertices=vertices, faces=faces)
        buffer.seek(0)
        return buffer.getvalue()

    @property
    def trans_mat(self) -> np.ndarray:
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
    def viewer_verts(self) -> np.ndarray:
        verts = self.vertices[self.current_frame]
        ones = np.ones((verts.shape[0], 1))
        hom = np.concatenate([verts, ones], axis=1)
        transformed = (self.trans_mat @ hom.T).T
        return transformed[:, :3]

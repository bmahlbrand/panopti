# panopti/objects/mesh.py
import io
import numpy as np

from typing import Dict, Any, Optional, Tuple, List
from .base import SceneObject

class Mesh(SceneObject):
    def __init__(self, viewer, vertices, faces, name: str,
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
        )

        self.vertices = self._convert_to_list(vertices)
        self.faces = self._convert_to_list(faces)
        self.wireframe = wireframe
        self.visible = visible
        self.opacity = opacity
        self.position = position
        self.rotation = rotation
        self.scale = scale
        self.color = color
        self.vertex_colors = self._convert_to_list(vertex_colors) if vertex_colors is not None else None
        self.face_colors = self._convert_to_list(face_colors) if face_colors is not None else None
    
    def _convert_to_list(self, data):
        if isinstance(data, np.ndarray):
            return data.tolist()
        return data
    
    def to_dict(self) -> Dict[str, Any]:
        data = {
            "id": self.name,
            "name": self.name,
            "type": "mesh",
            "vertices": self.vertices,
            "faces": self.faces,
            "wireframe": self.wireframe,
            "visible": self.visible,
            "opacity": self.opacity,
            "position": self.position,
            "rotation": self.rotation,
            "scale": self.scale,
            "color": self.color,
            "vertex_colors": self.vertex_colors,
            "face_colors": self.face_colors,
            "warnings": self.warnings,
        }
        return self._sanitize_for_json(data)

    @property
    def trans_mat(self) -> np.ndarray:
        """Returns the 4x4 transformation matrix corresponding to 
        the object's position, rotation, and scale in the viewer."""
        tx, ty, tz = np.asarray(self.position, dtype=np.float32)
        rx, ry, rz = np.asarray(self.rotation, dtype=np.float32)
        sx, sy, sz = np.asarray(self.scale, dtype=np.float32)

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
        """Returns the Mesh's vertices under the transformation given by `trans_mat`."""
        verts = np.array(self.vertices)
        ones = np.ones((verts.shape[0], 1))
        hom = np.concatenate([verts, ones], axis=1)
        transformed = (self.trans_mat @ hom.T).T
        return transformed[:, :3]

    def export(self) -> str:
        """Export mesh to OBJ format string using trimesh."""
        try:
            import trimesh
        except ImportError:
            raise ImportError("trimesh is required for exporting to OBJ format. Please install it with 'pip install trimesh'.")

        vertices = np.array(self.vertices)
        faces = np.array(self.faces)

        # Use trimesh to export
        mesh = trimesh.Trimesh(vertices=vertices, faces=faces)
        
        # Add vertex colors if available
        if self.vertex_colors is not None:
            vertex_colors = np.array(self.vertex_colors)
            # Convert to 0-255 range if in 0-1 range
            if vertex_colors.max() <= 1.0:
                vertex_colors = (vertex_colors * 255).astype(np.uint8)
            mesh.visual.vertex_colors = vertex_colors
        
        # Add face colors if available  
        if self.face_colors is not None:
            face_colors = np.array(self.face_colors)
            # Convert to 0-255 range if in 0-1 range
            if face_colors.max() <= 1.0:
                face_colors = (face_colors * 255).astype(np.uint8)
            mesh.visual.face_colors = face_colors
        
        # Export to OBJ string
        f = io.BytesIO()
        mesh.export(file_obj=f, file_type='obj')
        f.seek(0)
        return f.read()
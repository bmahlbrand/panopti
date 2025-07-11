# panopti/objects/mesh.py
import io
import numpy as np

from typing import Dict, Any, Optional, Tuple, List, Union
from .base import SceneObject
from panopti.materials import MaterialPresets

class Mesh(SceneObject):
    def __init__(self, 
                viewer, 
                vertices, 
                faces,
                name: str,
                visible: bool = True,
                position: Union[Tuple[float, float, float], np.ndarray] = (0, 0, 0),
                rotation: Union[Tuple[float, float, float], np.ndarray] = (0, 0, 0),
                scale: Union[Tuple[float, float, float], np.ndarray] = (1.0, 1.0, 1.0),
                vertex_colors: Optional[Union[List[Tuple[float, float, float]], np.ndarray]] = None,
                face_colors: Optional[Union[List[Tuple[float, float, float]], np.ndarray]] = None,
                material: Optional[Any] = None):
        super().__init__(viewer, name)

        self._check_for_nans(
            vertices=vertices,
            faces=faces,
            vertex_colors=vertex_colors,
            face_colors=face_colors,
            position=position,
            rotation=rotation,
            scale=scale,
        )

        # Store as numpy arrays internally
        self.vertices = np.asarray(vertices, dtype=np.float32)
        self.faces = np.asarray(faces, dtype=np.int32)
        self.visible = visible
        self.position = np.asarray(position, dtype=np.float32)
        self.rotation = np.asarray(rotation, dtype=np.float32)
        self.scale = np.asarray(scale, dtype=np.float32)
        self.vertex_colors = np.asarray(vertex_colors, dtype=np.float32) if vertex_colors is not None else None
        self.face_colors = np.asarray(face_colors, dtype=np.float32) if face_colors is not None else None
        self.material = material or MaterialPresets.default

    
    def to_dict(self, serialize: bool = True) -> Dict[str, Any]:
        data = {
            "id": self.name,
            "name": self.name,
            "type": "mesh",
            "vertices": self.vertices,
            "faces": self.faces,
            "visible": self.visible,
            "position": self.position,
            "rotation": self.rotation,
            "scale": self.scale,
            "vertex_colors": self.vertex_colors,
            "face_colors": self.face_colors,
            "warnings": self.warnings,
        }
        
        # Add material data if present
        if self.material is not None:
            data["material"] = self.material.to_dict()
        
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
    def viewer_verts(self) -> np.ndarray:
        """Returns the Mesh's vertices under the transformation given by `trans_mat`."""
        verts = self.vertices
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

        vertices = self.vertices
        faces = self.faces

        # Use trimesh to export
        mesh = trimesh.Trimesh(vertices=vertices, faces=faces)
        
        # Add vertex colors if available
        if self.vertex_colors is not None:
            vertex_colors = self.vertex_colors
            # Convert to 0-255 range if in 0-1 range
            if vertex_colors.max() <= 1.0:
                vertex_colors = (vertex_colors * 255).astype(np.uint8)
            mesh.visual.vertex_colors = vertex_colors
        
        # Add face colors if available  
        if self.face_colors is not None:
            face_colors = self.face_colors
            # Convert to 0-255 range if in 0-1 range
            if face_colors.max() <= 1.0:
                face_colors = (face_colors * 255).astype(np.uint8)
            mesh.visual.face_colors = face_colors
        
        # Export to OBJ string
        f = io.BytesIO()
        mesh.export(file_obj=f, file_type='obj')
        f.seek(0)
        return f.read()
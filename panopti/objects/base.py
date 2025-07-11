# panopti/objects/base.py
from typing import Any, Dict
import numpy as np
import math
import numbers
from ..utils.parse import as_list, as_array
from panopti.materials.base import BaseMaterial

class SceneObject:
    def __init__(self, viewer, name: str):
        self.viewer = viewer
        self.name = name
        self.visible = True
        self.warnings = []

    def _check_for_nans(self, **kwargs) -> None:
        """Check numeric values for NaNs and record warnings."""
        for attr, value in kwargs.items():
            if value is None:
                continue
            if isinstance(value, np.ndarray):
                if np.isnan(value).any():
                    msg = f"NaN detected in {attr}"
                    if msg not in self.warnings:
                        self.warnings.append(msg)
                continue
            # For non-ndarray values, try to convert to array and check
            try:
                arr = np.asarray(value, dtype=float)
                if np.isnan(arr).any():
                    msg = f"NaN detected in {attr}"
                    if msg not in self.warnings:
                        self.warnings.append(msg)
            except Exception:
                continue
    
    def _sanitize_for_json(self, value):
        """Convert NaNs to ``None`` for JSON serialization using simple loops."""

        if isinstance(value, np.ndarray):
            arr = value
            if np.issubdtype(arr.dtype, np.floating):
                arr = np.where(np.isnan(arr), None, arr)
            return arr.tolist()

        if isinstance(value, numbers.Number):
            if isinstance(value, float) and math.isnan(value):
                return None
            # Convert numpy scalars to Python scalars
            if isinstance(value, np.generic):
                return value.item()
            return value

        if isinstance(value, dict):
            sanitized = {}
            for k, v in value.items():
                sanitized[k] = self._sanitize_for_json(v)
            return sanitized

        if isinstance(value, (list, tuple)):
            return [self._sanitize_for_json(v) for v in value]

        return value

    def _to_serializable(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Convert object data to JSON-serialisable format for socket transmission."""
        # First sanitize for NaNs, then convert to lists
        sanitized = self._sanitize_for_json(data)
        return as_list(sanitized)

    def _from_serializable(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Convert serialised data back to numpy arrays for internal use."""
        return as_array(data)

    def update(self, **kwargs) -> None:
        """Updates this object's attributes and propagate updates to the viewer."""
        converted_kwargs = {}
        for key, value in kwargs.items():
            if hasattr(self, key):
                if isinstance(value, BaseMaterial):
                    # For materials, use the raw dict without converting to arrays
                    converted_kwargs[key] = value.to_dict()
                    setattr(self, key, value)
                else:
                    converted_kwargs[key] = as_array(value)
                    setattr(self, key, converted_kwargs[key])

        self._check_for_nans(**converted_kwargs)
        data = dict(converted_kwargs)
        if self.warnings:
            data['warnings'] = self.warnings
        sanitized = self._to_serializable(data)
        self.viewer.socket_manager.emit_update_object(self, sanitized, raw_data=data)
    
    def delete(self) -> None:
        if self.name in self.viewer.objects:
            del self.viewer.objects[self.name]
        
        self.viewer.socket_manager.emit_delete_object(self.name)
    
    def to_dict(self) -> Dict[str, Any]:
        raise NotImplementedError("Subclasses must implement to_dict()")
    
    def export(self) -> bytes:
        """Export the object to file."""
        raise NotImplementedError("Subclasses must implement export()")
    
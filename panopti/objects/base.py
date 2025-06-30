# panopti/objects/base.py
from typing import Any, Dict
import numpy as np
import math
import numbers

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
            try:
                arr = np.asarray(value, dtype=float)
            except Exception:
                continue
            if np.isnan(arr).any():
                msg = f"NaN detected in {attr}"
                if msg not in self.warnings:
                    self.warnings.append(msg)
    
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
            return float(value) if isinstance(value, np.generic) else value

        if isinstance(value, dict):
            sanitized = {}
            for k, v in value.items():
                sanitized[k] = self._sanitize_for_json(v)
            return sanitized

        if isinstance(value, (list, tuple)):
            return [self._sanitize_for_json(v) for v in value]

        return value

    def update(self, **kwargs) -> None:
        """UUpdates this object's attributes and propagate updates to the viewer."""
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)

        self._check_for_nans(**kwargs)
        data = dict(kwargs)
        if self.warnings:
            data['warnings'] = self.warnings
        sanitized = self._sanitize_for_json(data)

        self.viewer.socket_manager.emit_update_object(self, sanitized)
    
    def delete(self) -> None:
        if self.name in self.viewer.objects:
            del self.viewer.objects[self.name]
        
        self.viewer.socket_manager.emit_delete_object(self.name)
    
    def to_dict(self) -> Dict[str, Any]:
        raise NotImplementedError("Subclasses must implement to_dict()")
    
    def export(self) -> bytes:
        """Export the object to file."""
        raise NotImplementedError("Subclasses must implement export()")
    
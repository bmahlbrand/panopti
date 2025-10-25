# panopti/ui/controls.py
from typing import Callable, Dict, Any, Optional, List, Tuple
import numpy as np
from ..utils.parse import as_array, as_list

class UIControl:
    def __init__(self, viewer, name: str):
        self.viewer = viewer
        self.name = name
        self.group = None  # Which group this control belongs to
    
    def handle_event(self, value: Any = None) -> Optional[str]:
        raise NotImplementedError("Subclasses must implement handle_event()")
    
    def to_dict(self) -> Dict[str, Any]:
        raise NotImplementedError("Subclasses must implement to_dict()")
    
    def value(self) -> Any:
        """Get the current value of the UI control"""
        raise NotImplementedError("Subclasses must implement value()")
    
    def _add_common_fields(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Add common fields to the control data dictionary"""
        if self.group is not None:
            data['group'] = self.group
        if hasattr(self.viewer, 'viewer_id'):
            data['viewer_id'] = self.viewer.viewer_id
        return data
    
    def delete(self) -> None:
        if self.name in self.viewer.ui_controls:
            del self.viewer.ui_controls[self.name]
        
        self.viewer.socket_manager.emit_delete_control(self.name)


class Group(UIControl):
    """A collapsible group that can contain other UI controls"""
    def __init__(self, viewer, name: str, collapsed: bool = False):
        super().__init__(viewer, name)
        self.collapsed = collapsed
        self.controls = []  # List of control names in this group
    
    def handle_event(self, value: Any = None) -> Optional[str]:
        # Groups don't have events themselves
        return None
    
    def value(self) -> bool:
        """Get the current collapsed state"""
        return self.collapsed
    
    def add_control(self, control: UIControl) -> None:
        """Add a control to this group"""
        control.group = self.name
        self.controls.append(control.name)
    
    def to_dict(self) -> Dict[str, Any]:
        data = {
            "id": self.name,
            "name": self.name,
            "type": "group",
            "collapsed": self.collapsed,
            "controls": self.controls
        }
        
        if hasattr(self.viewer, 'viewer_id'):
            data['viewer_id'] = self.viewer.viewer_id
        
        return data


class Slider(UIControl):
    def __init__(self, viewer, callback: Callable, name: str,
                min: float = 0.0, max: float = 1.0, step: float = 0.1,
                initial: float = 0.5, description: str = ""):
        super().__init__(viewer, name)
        
        self.callback = callback
        self.min = min
        self.max = max
        self.step = step
        self.initial = initial
        self.description = description
        self.current_value = initial
    
    def handle_event(self, value: float) -> Optional[str]:
        self.current_value = float(value)
        if self.callback:
            return self.callback(self.viewer, self.current_value)
        return None
    
    def value(self) -> float:
        """Get the current value of the slider"""
        return self.current_value
    
    def to_dict(self) -> Dict[str, Any]:
        data = {
            "id": self.name,
            "name": self.name,
            "type": "slider",
            "min": float(self.min),
            "max": float(self.max),
            "step": float(self.step),
            "initial": float(self.initial),
            "description": self.description
        }
        
        return self._add_common_fields(data)


class Button(UIControl):
    def __init__(self, viewer, callback: Callable, name: str):
        super().__init__(viewer, name)
        self.callback = callback
    
    def handle_event(self, value: Any = None) -> None:
        if self.callback:
            self.callback(self.viewer)
    
    def value(self) -> int:
        return 0
    
    def to_dict(self) -> Dict[str, Any]:
        data = {
            "id": self.name,
            "name": self.name,
            "type": "button"
        }
        
        return self._add_common_fields(data)


class Label(UIControl):
    def __init__(self, viewer, callback: Callable, name: str, text: str = ''):
        super().__init__(viewer, name)
        self.callback = callback
        self.text = text
    
    def handle_event(self, value: Any = None) -> None:
        return None
    
    def value(self) -> str:
        """Get the current text of the label"""
        return self.text
    
    def update(self, text) -> None:
        self.text = text
        if self.callback: self.callback(self.viewer)
        self.viewer.socket_manager.emit_update_label(self.name, text)
    
    def to_dict(self) -> Dict[str, Any]:
        data = {
            "id": self.name,
            "name": self.name,
            "type": "label",
            "text": self.text
        }
        
        return self._add_common_fields(data)


class Checkbox(UIControl):
    def __init__(self, viewer, callback: Callable, name: str,
                initial: bool = False, description: str = ""):
        super().__init__(viewer, name)
        
        self.callback = callback
        self.initial = initial
        self.description = description
        self.checked = initial
    
    def handle_event(self, value: bool) -> Optional[str]:
        self.checked = bool(value)
        if self.callback:
            return self.callback(self.viewer, self.checked)
        return None
    
    def value(self) -> bool:
        """Get the current checked state of the checkbox"""
        return self.checked
    
    def to_dict(self) -> Dict[str, Any]:
        data = {
            "id": self.name,
            "name": self.name,
            "type": "checkbox",
            "initial": bool(self.initial),
            "description": self.description
        }
        
        return self._add_common_fields(data)


class Dropdown(UIControl):
    def __init__(self, viewer, callback: Callable, name: str,
                options: List[str], initial: str = None, description: str = ""):
        super().__init__(viewer, name)
        
        self.callback = callback
        self.options = options
        self.initial = initial if initial is not None else (options[0] if options else "")
        self.description = description
        self.current_value = self.initial
    
    def handle_event(self, value: str) -> Optional[str]:
        self.current_value = str(value) 
        if self.callback:
            return self.callback(self.viewer, self.current_value)
        return None
    
    def value(self) -> str:
        """Get the current selected value of the dropdown"""
        return self.current_value
    
    def to_dict(self) -> Dict[str, Any]:
        data = {
            "id": self.name,
            "name": self.name,
            "type": "dropdown",
            "options": self.options,
            "initial": str(self.initial),
            "description": self.description
        }
        
        return self._add_common_fields(data)


class DownloadButton(UIControl):
    def __init__(self, viewer, callback: Callable, name: str, filename: str = 'download.bin'):
        super().__init__(viewer, name)

        self.callback = callback
        self.filename = filename

    def handle_event(self, value: Any = None) -> None:
        if self.callback:
            result = self.callback(self.viewer)
            if result is not None:
                try:
                    data = result.read()
                except AttributeError:
                    data = bytes(result)
                self.viewer.socket_manager.emit_download_file(data, self.filename)

    def value(self) -> int:
        return 0

    def to_dict(self) -> Dict[str, Any]:
        data = {
            "id": self.name,
            "name": self.name,
            "type": "download_button"
        }

        return self._add_common_fields(data)


class ColorPicker(UIControl):
    def __init__(self, viewer, callback: Callable, name: str,
                 initial: Tuple[float, float, float, float] = (0.5, 0.5, 0.5, 1.0)):
        super().__init__(viewer, name)

        self.callback = callback
        self.initial = np.asarray(initial, dtype=np.float32)
        self.current_value = np.asarray(initial, dtype=np.float32)

    def handle_event(self, value: Tuple[float, float, float, float]) -> Optional[str]:
        self.current_value = np.asarray(value, dtype=np.float32)
        if self.callback:
            return self.callback(self.viewer, self.current_value)
        return None

    def value(self) -> np.ndarray:
        return self.current_value

    def to_dict(self) -> Dict[str, Any]:
        data = {
            "id": self.name,
            "name": self.name,
            "type": "color_picker",
            "initial": self.initial,
        }

        return self._add_common_fields(data)


class PlotlyPlot(UIControl):
    def __init__(self, viewer, spec: Dict[str, Any], name: str):
        super().__init__(viewer, name)
        self.spec = spec

    def handle_event(self, value: Any = None) -> None:
        return None

    def value(self) -> Dict[str, Any]:
        return self.spec

    def to_dict(self) -> Dict[str, Any]:
        data = {
            "id": self.name,
            "name": self.name,
            "type": "plotly",
            "spec": self.spec
        }

        return self._add_common_fields(data)

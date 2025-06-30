# panopti/viewer.py
import threading
import numpy as np
import time
import uuid
from typing import Dict, Any, Callable, Optional, Tuple, List, Union
import os
import sys
import eventlet
from eventlet import event

from .server.app import create_app
from .comms.websocket import SocketManager, RemoteSocketIO
from .events import EventDispatcher
from .objects.mesh import Mesh
from .objects.animated_mesh import AnimatedMesh
from .objects.points import Points
from .objects.arrows import Arrows
from .ui.controls import Slider, Button, Label, Checkbox, Dropdown, DownloadButton, PlotlyPlot, ColorPicker

class BaseViewer:
    """Base class for both standalone and client viewers"""
    def __init__(self):
        self.objects = {}
        self.ui_controls = {}
        self.socket_manager = SocketManager(self)

        self.events = EventDispatcher(self)

        self._camera_thread = threading.Event()
        self._camera_data = None
        self._selected_object_thread = threading.Event()
        self._selected_object = None

    def capture_prints(self, buffer=None, capture_stderr=False):
        """Mirrors prints in the viewer."""
        from .utils.print_capture import capture_prints as cap

        def _callback(data: str):
            self.socket_manager.emit_console_output(data)

        return cap(buffer=buffer, capture_stderr=capture_stderr, callback=_callback)

    def hold(self):
        """Keep the script alive"""
        evt = event.Event()
        try:
            evt.wait()            # blocks until someone calls evt.send()
        except KeyboardInterrupt:
            print("Exiting…")

    def restart(self):
        """Restart the current Python process."""
        print("Restarting script...")
        module = getattr(sys.modules['__main__'], '__spec__', None)
        module = module.name if module and module.name else None

        if module:
            args = [sys.executable, '-m', module] + sys.argv[1:]
        else:
            args = [sys.executable] + sys.argv

        os.execv(sys.executable, args)

    def _add_control(self, cls, **kwargs):
        """Create a UI control and register it with the server."""
        control = cls(viewer=self, **kwargs)
        self.ui_controls[control.name] = control
        self.socket_manager.emit_add_control(control)
        return control
    
    def add_mesh(self, vertices: np.ndarray, faces: np.ndarray, name: str, wireframe: bool = False,
                visible: bool = True, opacity: float = 1.0,
                position: Tuple[float, float, float] = (0, 0, 0),
                rotation: Tuple[float, float, float] = (0, 0, 0),
                scale: Tuple[float, float, float] = (1, 1, 1),
                color: Tuple[float, float, float] = (0.5, 0.5, 0.5),
                vertex_colors: np.ndarray = None,
                face_colors: np.ndarray = None) -> Mesh:
        """Adds a Mesh object to the viewer.

        Parameters:
            vertices: (V, 3) array of vertex coordinates.
            faces: (F, 3) array of face indices.
            name: Name for the mesh.
            wireframe: Whether to render the mesh as a wireframe.
            visible: Whether the mesh is visible.
            opacity: Opacity of the mesh.
            position: Position of the mesh (XYZ).
            rotation: Rotation of the mesh (XYZ).
            scale: Scale of the mesh in (XYZ).
            color: Uniform RGB color of the mesh.
            vertex_colors: (V, 3) array of vertex colors.
            face_colors: (F, 3) array of face colors.

        Returns:
            Mesh: The created panopti mesh object.
        """
        if name is None:
            name = f"mesh_{uuid.uuid4().hex[:8]}"
        
        mesh = Mesh(
            viewer=self,
            vertices=vertices,
            faces=faces,
            name=name,
            wireframe=wireframe,
            visible=visible,
            opacity=opacity,
            position=position,
            rotation=rotation,
            scale=scale,
            color=color,
            vertex_colors=vertex_colors,
            face_colors=face_colors
        )
        
        self.objects[name] = mesh
        self.socket_manager.emit_add_geometry(mesh)
        
        return mesh
    
    def add_animated_mesh(self, vertices: np.ndarray, faces: np.ndarray, name: str, framerate: float = 24.0,
                         wireframe: bool = False, visible: bool = True, opacity: float = 1.0,
                         position: Tuple[float, float, float] = (0, 0, 0),
                         rotation: Tuple[float, float, float] = (0, 0, 0),
                         scale: Tuple[float, float, float] = (1, 1, 1),
                         color: Tuple[float, float, float] = (0.5, 0.5, 0.5),
                         vertex_colors: np.ndarray = None,
                         face_colors: np.ndarray = None) -> AnimatedMesh:
        """Adds an AnimatedMesh object to the viewer.

        Parameters:
            vertices: (T, V, 3) array of vertex coordinates for each frame.
            faces: (F, 3) array of face indices.
            name: Name for the animated mesh.
            framerate: Framerate for the animation.
            wireframe: Whether to render the mesh as a wireframe.
            visible: Whether the mesh is visible.
            opacity: Opacity of the mesh.
            position: Position of the mesh (XYZ).
            rotation: Rotation of the mesh (XYZ).
            scale: Scale of the mesh in (XYZ).
            color: Uniform RGB color of the mesh.
            vertex_colors: (V, 3) array of vertex colors.
            face_colors: (F, 3) array of face colors.

        Returns:
            AnimatedMesh: The created panopti animated mesh object.
        """

        if name is None:
            name = f"animated_mesh_{uuid.uuid4().hex[:8]}"
        
        animated_mesh = AnimatedMesh(
            viewer=self,
            vertices=vertices,
            faces=faces,
            name=name,
            framerate=framerate,
            wireframe=wireframe,
            visible=visible,
            opacity=opacity,
            position=position,
            rotation=rotation,
            scale=scale,
            color=color,
            vertex_colors=vertex_colors,
            face_colors=face_colors
        )
        
        self.objects[name] = animated_mesh
        self.socket_manager.emit_add_geometry(animated_mesh)
        
        return animated_mesh
    
    def add_points(self, points: np.ndarray, name: str,
                 colors: np.ndarray = (0.5, 0.5, 0.5),
                 size: float = 0.01, visible: bool = True, opacity: float = 1.0) -> Points:
        """Adds a Point Cloud object to the viewer.

        Parameters:
            points: (N, 3) array of point coordinates.
            name: Name for the points object.
            colors: (N, 3) or (3,) array of RGB colors for the points.
            size: Size of the points.
            visible: Whether the points are visible.
            opacity: Opacity of the points.

        Returns:
            Points: The created panopti points object.
        """
        if name is None:
            name = f"points_{uuid.uuid4().hex[:8]}"
        
        points_obj = Points(
            viewer=self,
            points=points,
            name=name,
            colors=colors,
            size=size,
            visible=visible,
            opacity=opacity
        )
        
        self.objects[name] = points_obj
        self.socket_manager.emit_add_geometry(points_obj)
        
        return points_obj
    
    def add_arrows(self, starts: np.ndarray, ends: np.ndarray, name: str,
                 color: np.ndarray = (0, 0, 0),
                 width: float = 0.01, visible: bool = True, opacity: float = 1.0) -> Arrows:
        """Adds an Arrows object to the viewer.

        Parameters:
            starts: (N, 3) array of start points for the arrows.
            ends: (N, 3) array of end points for the arrows.
            name: Name for the arrows object.
            color: (N, 3) or (3,) array of RGB colors for the arrows.
            width: Width of the arrows.
            visible: Whether the arrows are visible.
            opacity: Opacity of the arrows.

        Returns:
            Arrows: The created panopti arrows object.
        """
        if name is None:
            name = f"arrows_{uuid.uuid4().hex[:8]}"
        
        arrows_obj = Arrows(
            viewer=self,
            starts=starts,
            ends=ends,
            name=name,
            color=color,
            width=width,
            visible=visible,
            opacity=opacity
        )
        
        self.objects[name] = arrows_obj
        self.socket_manager.emit_add_geometry(arrows_obj)
        
        return arrows_obj
    
    def slider(self, callback: Callable, name: str, min: float = 0.0, max: float = 1.0,
              step: float = 0.1, initial: float = 0.5, description: str = "") -> Slider:
        
        return self._add_control(
            Slider,
            callback=callback,
            name=name,
            min=min,
            max=max,
            step=step,
            initial=initial,
            description=description,
        )
    
    def button(self, callback: Callable, name: str) -> Button:
        
        return self._add_control(Button, callback=callback, name=name)

    def download_button(self, callback: Callable, name: str, filename: str = 'download.bin') -> DownloadButton:

        return self._add_control(
            DownloadButton,
            callback=callback,
            name=name,
            filename=filename,
        )
    
    def label(self, callback: Callable, name: str = None, text: str = '') -> Label:
        
        if name is None:
            name = f"label_{uuid.uuid4().hex[:8]}"
        
        return self._add_control(
            Label,
            callback=callback,
            name=name,
            text=text,
        )
    
    def checkbox(self, callback: Callable, name: str, initial: bool = False,
                 description: str = "") -> Checkbox:
        
        return self._add_control(
            Checkbox,
            callback=callback,
            name=name,
            initial=initial,
            description=description,
        )
    
    def dropdown(self, callback: Callable, name: str, options: List[str],
                 initial: str = None, description: str = "") -> Dropdown:
        
        return self._add_control(
            Dropdown,
            callback=callback,
            name=name,
            options=options,
            initial=initial,
            description=description,
        )

    def color_picker(self, callback: Callable, name: str,
                     initial: Tuple[float, float, float, float] = (0.5, 0.5, 0.5, 1.0)) -> ColorPicker:

        return self._add_control(
            ColorPicker,
            callback=callback,
            name=name,
            initial=initial,
        )

    def add_plotly(self, spec: Dict[str, Any], name: str) -> PlotlyPlot:
        from plotly.utils import PlotlyJSONEncoder
        import json
        
        spec = json.loads(json.dumps(spec, cls=PlotlyJSONEncoder))
        plot = PlotlyPlot(viewer=self, spec=spec, name=name)
        self.ui_controls[name] = plot
        self.socket_manager.emit_add_control(plot)
        return plot
    
    def get(self, name: str) -> Any:
        return self.objects.get(name) or self.ui_controls.get(name)
    
    def handle_ui_event(self, event_type: str, control_id: str, value: Any = None):
        control = self.ui_controls.get(control_id)
        if control is None:
            return
        control.handle_event(value)

class ViewerClient(BaseViewer):
    """Client that connects to an existing panopti server"""
    def __init__(self, server_url: str = None, viewer_id: str = None):
        super().__init__()
        
        if not viewer_id:
            viewer_id = f"viewer_{uuid.uuid4().hex[:8]}"
        
        self.viewer_id = viewer_id
        
        # Default to localhost:8080 if no server URL provided
        if not server_url:
            server_url = "http://localhost:8080"
        elif not server_url.startswith(("http://", "https://")):
            server_url = f"http://{server_url}"

        base_url = server_url
        
        # Add viewer_id as a query parameter to ensure it's available in the web client
        if viewer_id and '?' not in server_url:
            server_url = f"{server_url}?viewer_id={viewer_id}"

        self.server_url = base_url.split('?')[0]
        
        print(f"Creating client connecting to: {server_url}")
        self.client = RemoteSocketIO(server_url, viewer_id)
        self.client.viewer = self  # Set the viewer reference
        self.client.connect()

        # Register handlers for incoming messages:
        self.client.on('ui_event_response', self.handle_ui_event_from_server)
        self.client.on('update_object', self.handle_update_object)
        self.client.on('restart_script', self.handle_restart_script)

        # State requests:
        self.client.on('request_state_from_client', self.handle_request_state)

        self._request_events = ['camera_info', 'selected_object']
        self._request_threads = {k: threading.Event() for k in self._request_events}
        self._request_data = {k: None for k in self._request_events}
        for event in self._request_events:
            self.client.on(event, self.handle_state_request)

        # events:
        self.client.on('events.camera', self.handle_events_camera)
        self.client.on('events.inspect', self.handle_events_inspect)
        self.client.on('events.select_object', self.handle_events_select_object)
        # events.control is handled internally
        # events.update_object is handled internally
    
    def handle_ui_event_from_server(self, data):
        if data.get('viewer_id') != self.viewer_id:
            return
            
        event_type = data.get('eventType')
        control_id = data.get('controlId')
        value = data.get('value')
        
        self.handle_ui_event(event_type, control_id, value)
        self.events.trigger('control', control_id, value)

    def handle_update_object(self, data):
        if data.get('viewer_id') != self.viewer_id:
            return
        obj_id = data.get('id')
        updates = data.get('updates', {})
        obj = self.objects.get(obj_id)
        if not obj:
            return
        for key, value in updates.items():
            if hasattr(obj, key):
                setattr(obj, key, value)
        self.events.trigger('update_object', obj_id, updates)

    def handle_restart_script(self, data):
        if data.get('viewer_id') != self.viewer_id:
            return
        self.restart()

    # --- Requesting state: ---
    def handle_request_state(self, data=None):
        """Send all current objects and UI controls to the client"""
        
        # Send all objects
        for obj in self.objects.values():
            if hasattr(obj, 'to_dict'):
                self.socket_manager.emit_add_geometry(obj)
        
        # Send all UI controls
        for control in self.ui_controls.values():
            if hasattr(control, 'to_dict'):
                self.socket_manager.emit_add_control(control)

    def camera(self, timeout: float = 1.0) -> Optional[Dict[str, Any]]:
        """Return the current camera parameters as a dictionary."""
        self.emit_state_request({'event': 'request_camera_info', 'viewer_id': self.viewer_id})
        if self._request_threads['camera_info'].wait(timeout):
            return self._request_data['camera_info']
        return None
    
    def selected_object(self, timeout: float = 1.0) -> Optional[str]:
        """Return the currently selected object name."""
        self.emit_state_request({'event': 'request_selected_object', 'viewer_id': self.viewer_id})
        if self._request_threads['selected_object'].wait(timeout):
            return self._request_data['selected_object']
        return None

    def emit_state_request(self, data):
        """Handle state requests from the server."""
        if data.get('viewer_id') != self.viewer_id:
            return
        
        event = data.get('event') # e.g. : 'request_camera_info'
        event_basename = event.replace('request_', '') # 'camera_info'
        if event_basename not in self._request_events:
            raise ValueError(f"Unknown state request event: {event}")
        
        self._request_threads[event_basename].clear()
        self._request_data[event_basename] = None
        self.socket_manager.emit('relay_state_request', {'event': event, 'viewer_id': self.viewer_id})

    def handle_state_request(self, data):
        """Handle incoming state from the frontend."""
        if data.get('viewer_id') != self.viewer_id:
            return
        
        event = data.get('event') # e.g. : 'request_camera_info'
        event_basename = event.replace('request_', '') # 'camera_info'
        if event_basename not in self._request_events:
            raise ValueError(f"Unknown state request event: {event}")
        
        self._request_data[event_basename] = data.get('data')
        self._request_threads[event_basename].set()

    #  --- Panopti events: ---
    def handle_events_camera(self, data):
        if data.get('viewer_id') != self.viewer_id:
            return
        camera_data = data.get('camera')
        self.events.trigger('camera', camera_data)

    def handle_events_inspect(self, data):
        if data.get('viewer_id') != self.viewer_id:
            return
        inspection_data = data.get('inspection')
        self.events.trigger('inspect', inspection_data)

    def handle_events_select_object(self, data):
        if data.get('viewer_id') != self.viewer_id:
            return
        selected_object = data.get('selected_object')
        self.events.trigger('select_object', selected_object)

class ViewerServer:
    """Standalone server without viewer functionality"""
    def __init__(self, host: str = 'localhost', port: int = 8080, debug: bool = False):
        self.host = host
        self.port = port
        self.debug = debug
        
        from .server.app import run_standalone_server
        run_standalone_server(host=host, port=port, debug=debug)


def connect(server_url: str = None, viewer_id: str = None) -> ViewerClient:
    """Connect to an existing panopti server"""
    return ViewerClient(server_url, viewer_id)


def start_server(host: str = 'localhost', port: int = 8080, debug: bool = False):
    """Start a standalone server without viewer functionality"""
    ViewerServer(host, port, debug)

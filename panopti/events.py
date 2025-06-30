from typing import Callable, Dict, List, Any

class EventDispatcher:
    """Event dispatcher used for viewer callbacks."""

    def __init__(self, viewer):
        self.viewer = viewer
        self._callbacks: Dict[str, List[Callable]] = {
            'camera': [],
            'inspect': []
        }

    def camera(self) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
        """The `camera` event is triggered when the user manipulates the viewer 
        camera (e.g. orbit, pan, zoom). This event provides a `dict` containing 
        information about the camera's current state.
         Example usage:
        ```python
        @viewer.events.camera()
        def camera_event(viewer, camera_info):
            print('Camera was updated!')
            # swivel scene mesh to always face the camera (in Y-axis):
            mesh = viewer.get('myMesh')
            mx, my, mz = mesh.position
            cx, cy, cz = camera_info['position']
            yaw = math.atan2(cx - mx, cz - mz)
            mesh.rotation = [0, yaw, 0]
            mesh.update(rotation=[0, yaw, 0])
        ```
        `camera_info` is a dict containing:

        | key        | meaning                                   | type  |
        |------------|-------------------------------------------|-------|
        | position   | camera world coords                       | list  |
        | rotation   | camera XYZ euler rotation                 | list  |
        | quaternion | camera rotation as quaternion             | list  |
        | up         | camera up-vector                          | list  |
        | target     | point the camera is looking at            | list  |
        | fov        | vertical field-of-view (degrees)          | float |
        | near       | near-plane distance                       | float |
        | far        | far-plane distance                        | float |
        | aspect     | viewport aspect ratio (w / h)             | float |
        """
        def decorator(func: Callable[[Any], Any]) -> Callable[[Any], Any]:
            self._callbacks.setdefault('camera', []).append(func)
            return func
        return decorator

    def inspect(self) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
        """The `inspect` event is triggered when the inspection tool is used in the viewer (e.g. when clicking on a mesh to inspect its local vertex indices).
        Example usage:
        ```python
        @viewer.events.inspect()
        def inspect_event(viewer, inspect_info):
            print(f"User clicked on a {inspect_info['object_type']} object.")
            if inspect_info['object'type'] == 'mesh':
                print('Selected face index: ', inspect_info['inspect_result']['face_index'])
        ```
        `inspect_info` is a dict containing:

        | key            | meaning                                                                                                                         | type   |
        |----------------|---------------------------------------------------------------------------------------------------------------------------------|--------|
        | object_name    | `name` attribute of selected object                                                                                             | str    |
        | object_type    | type of Panopti object selected (e.g., `'mesh'`, `'points'`)                                                               | str    |
        | world_coords   | XYZ world coordinates of the pick point                                                                                         | list   |
        | screen_coords  | integer pixel coordinates of the pick point                                                                                     | list   |
        | inspect_result | geometry‑specific data at the pick point:<br><br>**Mesh / AnimatedMesh**<br>&nbsp;&nbsp;• `face_index`: `int` (clicked face)<br>&nbsp;&nbsp;• `vertex_indices`: `list[int]` (three vertices of face)<br><br>**PointCloud**<br>&nbsp;&nbsp;• `point_index`: `int` (clicked point) | dict   |
        """
        def decorator(func: Callable[[Any], Any]) -> Callable[[Any], Any]:
            self._callbacks.setdefault('inspect', []).append(func)
            return func
        return decorator
    
    def select_object(self) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
        """The `select_object` event is triggered when a geometric structure is selected in the viewer -- either by clicking on the object directly or selecting it in the layers panel.
        Example usage:
        ```python
        @viewer.events.object_selection()
        def object_selection_event(viewer, object_name):
            print(f"User selected {object_name}")
        ```
        `object_name: str` is the selected object's name.
        """
        def decorator(func: Callable[[Any], Any]) -> Callable[[Any], Any]:
            self._callbacks.setdefault('select_object', []).append(func)
            return func
        return decorator
    
    def control(self) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
        """The `control` event is triggered when any control element is interacted with.
        Example usage:
        ```python
        @viewer.events.control()
        def control_event(viewer, control_name, value):
            print(f"User updated {control_name} to {value}")
        ```
        `control_name: str` is the selected object's name
        
        `value` is the control element's new value
        """
        def decorator(func: Callable[[Any], Any]) -> Callable[[Any], Any]:
            self._callbacks.setdefault('control', []).append(func)
            return func
        return decorator
    
    def update_object(self) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
        """The `update_object` event is triggered when any geometric object has an attribute updated, e.g. through `.update(...)`.
        Example usage:
        ```python
        @viewer.events.update_object()
        def update_object_event(viewer, object_name, data):
            print(f"Object {object_name} updated with attributes: {data.keys()}")
        ```
        `object_name: str` is the updated object's name
        
        `data: dict` holds the updated attributes of the object, e.g. `{'vertices': ...}`
        """
        def decorator(func: Callable[[Any], Any]) -> Callable[[Any], Any]:
            self._callbacks.setdefault('update_object', []).append(func)
            return func
        return decorator

    def trigger(self, event: str, *args, **kwargs) -> None:
        """Trigger all callbacks for a given event name."""
        for cb in self._callbacks.get(event, []):
            try:
                cb(self.viewer, *args, **kwargs)
            except Exception as exc:
                print(f'Error in {event} callback {cb}: {exc}')

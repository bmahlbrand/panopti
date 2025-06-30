# Panopti - interactive 3D visualization in Python
![Logo](./assets/banner.jpg)

## [ [Documentation](https://armanmaesumi.github.io/panopti/) ] - [ [PyPI](https://pypi.org/project/panopti/) ]

Panopti is a Python package for interactive 3D visualization that seamlessly supports remote development setups (e.g. through SSH). It pairs a Flask server with a React+ThreeJS frontend and is designed such that users only need to write Python code, making it painless to setup interactive experiments and scenes. All code examples and demos throughout the documentation are achieved purely using Panopti in Python -- no JavaScript required!.

Panopti supports various geometric data structures (e.g. meshes, point clouds), UI control elements (e.g. buttons, sliders, color pickers, interactive plots) that are programmable in Python, and global event callbacks (e.g. for camera movement, clicking on geometry).

Install from pip:
```
pip install panopti
```

# Simple example
First start a Panopti server in a separate terminal:
```bash
python -m panopti.run_server --host localhost --port 8080
```

Then you can easily define your scene, for example:
```python
import panopti
import trimesh # just for io

# create panopti client that connects to server:
viewer = panopti.connect(server_url="http://localhost:8080", viewer_id='client') 
# viewer at: http://localhost:8080/?viewer_id=client

mesh = trimesh.load('./examples/demosthenes.obj')
verts, faces = mesh.vertices, mesh.faces
verts = np.ascontiguousarray(verts, dtype=np.float32)
faces = np.ascontiguousarray(faces, dtype=np.int32)

# add a mesh to the scene:
viewer.add_mesh(
    vertices=verts,
    faces=faces,
    name="Statue",
    color=(0.8, 0.2, 0.2),
)

def callback_button(viewer):
    # Update the mesh's vertices
    statue = viewer.get('Statue')
    v = np.asarray(statue.vertices)
    v = v * 2.0 
    statue.update(vertices=v)

viewer.button(callback=callback_button, name='Click Me!')

viewer.hold() # prevent script from terminating
```
See `/examples` for more!

## Installation

To install from pip:
```bash
pip install panopti
```

To install from source:
```bash
git clone https://github.com/ArmanMaesumi/panopti
cd panopti/frontend 

# build frontend viewer
npm install
npm run build

# install python package
cd ..
pip install .
```

### Dependencies

Core dependencies:
```bash
pip install numpy eventlet requests flask flask-socketio
```

Optional dependencies:
```bash
pip install trimesh         # for exporting meshes
pip install matplotlib      # for colormap utilities
pip install plotly==5.22.0  # for plotly figure support
```

Doc-related dependencies:
```bash
pip install mkdocs mkdocs-material mkdocstrings mkdocstrings-python
```

--- 

#### Cite as

```bibtex
@misc{panopti,
  title = {Panopti},
  author = {Arman Maesumi},
  note = {https://github.com/ArmanMaesumi/panopti},
  year = {2025}
}
```
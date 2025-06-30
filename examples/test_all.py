# Test all major features in panopti package
import trimesh
import numpy as np
import panopti
import eventlet
import igl
import matplotlib.pyplot as plt
from matplotlib import cm
from panopti.utils import to_rgb

# Create a client that connects to external server
viewer_id = "client"
pano = panopti.connect(server_url="http://localhost:8080", viewer_id=viewer_id)
pano.capture_prints(capture_stderr=True)

mesh = trimesh.load('./examples/demosthenes.obj')
verts, faces = mesh.vertices, mesh.faces
verts = np.ascontiguousarray(verts, dtype=np.float32)
verts = verts - verts.mean(axis=0, keepdims=True)  # Center the mesh
faces = np.ascontiguousarray(faces, dtype=np.int32)
normals = np.ascontiguousarray(mesh.vertex_normals, dtype=np.float32)
V, F = verts.shape[0], faces.shape[0]

### Mesh
vertex_colors = to_rgb(verts[:, 1], cmap='viridis')
vertex_colors[0, :] = np.nan 
pano.add_mesh( # test NaN checks:
    vertices=verts - (4.0, 0.0, 0.0),
    faces=faces,
    name="StatueNaN",
    vertex_colors=vertex_colors,
)

vertex_colors = to_rgb(verts[:, 1], cmap='viridis')
pano.add_mesh(
    vertices=verts,
    faces=faces,
    name="StatueMesh",
    vertex_colors=vertex_colors,
)

### Point cloud
points = verts.copy()
points[:,0] += 2
point_colors = to_rgb(points[:, 0] + points[:, 1], cmap='viridis')
pano.add_points(
    points=points,
    name="StatuePoints",
    colors=point_colors,
    size=0.015,
)

### Arrows
points2 = points + (0.8, 0.8, -1.5)
random_subset = np.random.choice(points.shape[0], size=points.shape[0] // 128, replace=False)
pano.add_points(
    points=points2[random_subset],
    name="PointsSubset",
    colors=point_colors[random_subset],
    size=0.05,
)
pano.add_arrows(
    starts=points2[random_subset],
    ends=points[random_subset],
    name="Arrows",
    color=(0.01, 0.01, 0.01),
    width=0.01,
    # opacity=0.25
)


def callback_color_picker(viewer, color):
    # print(f"Color picked: {color}")
    mesh = viewer.get("StatueMesh")
    if mesh is not None:
        mesh.update(vertex_colors=None)
        mesh.update(color=(color[0], color[1], color[2]), opacity=color[3])

def whacky_transform(vertices: np.ndarray,
                     normals:  np.ndarray,
                     t:        float) -> np.ndarray:
    """
    vertices: (N,3) float32 array in unit‑sphere
    normals:  (N,3) float32 array, per‑vertex normals
    t:        [0..1] control knob
    returns:  new (N,3) array
    """
    # 1) swirl around Y: angle = t*2π * radius
    radii  = np.linalg.norm(vertices, axis=1)             # shape (N,)
    angles = radii * (t * 2*np.pi)                       # shape (N,)
    cosA   = np.cos(angles)[:,None]
    sinA   = np.sin(angles)[:,None]
    x, y, z = vertices[:,0:1], vertices[:,1:2], vertices[:,2:3]

    x_sw = x * cosA - z * sinA
    z_sw = x * sinA + z * cosA
    verts_swirl = np.concatenate([x_sw, y, z_sw], axis=1)

    # 2) pulsate along normals: sin(frequency*radius + phase) * amplitude
    freq      = 6.0                   # number of ripples
    amp_base  = 0.2                   # max offset
    phase     = t * np.pi             # phase shift
    offsets   = np.sin(radii * freq + phase) * amp_base * t
    verts_out = verts_swirl + normals * offsets[:,None]

    return verts_out

pano.slider(callback=lambda viewer, val: print(f"MySlider was set to: {val}!"), name='MySlider', min=0.0, max=1.0, initial=0.0, step=0.01, description='Here is a description')
pano.checkbox(callback=lambda viewer, val: print(f"MyCheckbox was set to: {val}!"), name='MyCheckbox', initial=True)
pano.dropdown(callback=lambda viewer, val: print(f"MyDropdown was set to: {val}!"), name='MyDropdown', options=['Option 1', 'Option 2', 'Option 3'], initial=0)
pano.button(callback=lambda viewer: print("MyButton was clicked!"), name='MyButton')
pano.color_picker(callback=callback_color_picker, name='MyColorPicker', initial=(0.5, 0.5, 0.5, 1.0))
pano.label(callback=None, name='label')
pano.get("label").update("And here is a label that can be *dynamically* updated! It also supports **markdown**!")
pano.button(callback=lambda viewer: viewer.get('SelfDestructiveButton').delete(), name='SelfDestructiveButton')
def test_request_states(viewer: panopti.viewer.ViewerClient):
    camera = viewer.camera()
    print(f"Camera position: {camera['position']}")
    selected_object = viewer.selected_object()
    print(f"Selected object: {selected_object}")
pano.button(callback=test_request_states, name='Test Selected Object')

def callback_download_button(viewer):
    print("Download button clicked!")
    # send a text file as a BytesIO object:
    import io
    text_data = "This is a test file."
    text_io = io.BytesIO(text_data.encode('utf-8'))
    bytes_data = text_io.getvalue()
    return bytes_data

pano.download_button(callback=callback_download_button, name='Download Text File', filename='test.txt')

def callback_test_state_functions(viewer):
    statue = viewer.get('StatueMesh')
    verts = np.asarray(statue.vertices)
    statue.update(vertices=verts + (0.0, 2.0, 0.0))

    statuenan = viewer.get('StatueNaN')
    if statuenan is not None:
        statuenan.delete()

    print(statue.trans_mat)

pano.button(callback=callback_test_state_functions, name='Test State Functions')

data = verts[:, 1]
counts, bins = np.histogram(data, bins=128)
bin_centers = 0.5 * (bins[:-1] + bins[1:])
widths = bins[1:] - bins[:-1]
import plotly.graph_objects as go
# build a bar chart with colors based on bin centers
fig = go.Figure(
    go.Bar(
        x=bin_centers,
        y=counts,
        width=widths,
        marker=dict(
            color=bin_centers,               # color by bin center
            colorscale='Viridis',            # choose any Plotly colormap
            showscale=False,                  # display the colorbar
            colorbar=dict(title='Bin value'),
            line=dict(width=0)
        ),
        showlegend=False
    )
)
fig.update_layout(
    margin=dict(l=0, r=0, t=20, b=0),
    title_text='Histogram of Statue Y-coordinates',
    xaxis_title='Statue Y-coordinates',
    yaxis_title='Count',
    showlegend=False,
)
fig.update_layout(title_font_size=12)
fig.update_layout(title_x=0.13, title_xanchor='left')
fig.update_xaxes(title_font_size=12, tickfont_size=8)
fig.update_yaxes(title_font_size=12, tickfont_size=8)
pano.add_plotly(fig.to_plotly_json(), name='Histogram')

# bake whacky animation:
verts_animation = []
for t in np.linspace(0, 1, 50):
    temp_verts = whacky_transform(verts.copy(), normals, t) - (2.0, 0.0, 0.0)
    verts_animation.append(temp_verts)
verts_animation = np.stack(verts_animation)
pano.add_animated_mesh(
    vertices=verts_animation,
    faces=faces,
    name="WhackyAnimation",
    framerate=15,
    vertex_colors=vertex_colors,
)

@pano.events.camera()
def camera_event(viewer, camera):
    print(f"Camera moved: {camera['position']}")

@pano.events.inspect()
def inspect_event(viewer, data):
    print(f"Inspect event: {data}")

@pano.events.select_object()
def select_object_event(viewer, data):
    print(f"Object selected: {data}")

@pano.events.control()
def control_event(viewer, control_id, value):
    print(f"Control {control_id} changed to {value}")

@pano.events.update_object()
def update_object_event(viewer, object_id, data):
    print(f"Object {object_id} updated with attributes: {data.keys()}")

pano.hold()

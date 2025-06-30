import panopti
import trimesh
import numpy as np
import plotly.graph_objects as go
from panopti.utils import to_rgb

viewer = panopti.connect(server_url="http://localhost:8080", viewer_id='client')

mesh = trimesh.load('./examples/demosthenes.obj')
verts, faces = mesh.vertices, mesh.faces

# Add a mesh
vertex_colors = to_rgb(verts[:, 1], cmap='viridis')
viewer.add_mesh(
    vertices=verts,
    faces=faces,
    name="Statue",
    vertex_colors=vertex_colors,
)

# --- Let's add some controls ---

# On button press, randomly rescale our mesh
def callback_random_rotate(viewer):
    random_rotation = np.random.uniform(0, 2 * np.pi, (3,))

    yaxis_only = viewer.get('Y-axis Only').value() # read checkbox value
    if yaxis_only: # zero out X,Z axes
        random_rotation[[0, 2]] = 0

    viewer.get('Statue').update(rotation=random_rotation)
    plot_histogram(viewer) # update histogram
viewer.button(callback=callback_random_rotate, name='Randomly rotate mesh')

# Checkbox will control if we uniformly scale or not -- we can leave the callback blank
viewer.checkbox(callback=None, name='Y-axis Only', initial=True)

# Override mesh color using a color picker:
def callback_recolor_mesh(viewer, color):
    mesh = viewer.get("Statue")
    if mesh is not None:
        mesh.update(vertex_colors=None)
        mesh.update(color=(color[0], color[1], color[2]), opacity=color[3])

viewer.color_picker(callback=callback_recolor_mesh, name='Recolor Mesh', initial=(0.5, 0.5, 0.5, 1.0))

# Slider that adds Gaussian noise to the mesh
def callback_add_noise(viewer, value):
    noise = value * np.random.randn(*verts.shape)
    new_verts = verts.copy() + noise
    viewer.get('Statue').update(vertices=new_verts)
    plot_histogram(viewer) # update histogram
viewer.slider(callback=callback_add_noise, name='GaussinNoiseSTD', min=0.0, max=0.2, initial=0.0, step=0.01)

# Let's plot a histogram of the mesh vertex y-coordinates:
def plot_histogram(viewer):
     # Get the y-coordinates of current mesh
    data = np.asarray(viewer.get('Statue').viewer_verts)[:,1]
    counts, bins = np.histogram(data, bins=128)
    bin_centers = 0.5 * (bins[:-1] + bins[1:])
    widths = bins[1:] - bins[:-1]
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
    viewer.add_plotly(fig.to_plotly_json(), name='Histogram')
plot_histogram(viewer)

# import math
# @viewer.events.camera()
# def camera_event(viewer, camera_info):
#     # print('Camera was updated!')
#     # swivel scene mesh to always face the camera (in Y-axis):
#     mesh = viewer.get('Statue')
#     mx, my, mz = mesh.position
#     cx, cy, cz = camera_info['position']
#     yaw = math.atan2(cx - mx, cz - mz)
#     mesh.rotation = [0, yaw, 0]
#     mesh.update(rotation=[0, yaw, 0])

viewer.hold()
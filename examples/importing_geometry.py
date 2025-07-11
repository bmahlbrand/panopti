import trimesh
import numpy as np
import panopti
from panopti.utils import to_rgb

viewer = panopti.connect(server_url='http://localhost:8080', viewer_id='client')

mesh = trimesh.load('./examples/demosthenes.obj')
verts, faces = mesh.vertices, mesh.faces
verts = np.ascontiguousarray(verts, dtype=np.float32)
faces = np.ascontiguousarray(faces, dtype=np.int32)
normals = np.ascontiguousarray(mesh.vertex_normals, dtype=np.float32)
verts = verts - verts.mean(axis=0, keepdims=True)  # Center the mesh

### Add mesh with vertex colors
vertex_colors = to_rgb(verts[:, 1], cmap='viridis')
viewer.add_mesh(
    vertices=verts,
    faces=faces,
    name="StatueMesh",
    vertex_colors=vertex_colors,
)

### Add Point cloud -- reuse vertex_colors
points = verts.copy()
points[:,0] += 2
viewer.add_points(
    points=points,
    name="StatuePoints",
    colors=vertex_colors,
    size=0.015,
)

### Add arrows pointing to another point cloud
points2 = points + (0.8, 0.8, -1.5)
random_subset = np.random.choice(points.shape[0], size=points.shape[0] // 128, replace=False)
viewer.add_points(
    points=points2[random_subset],
    name="PointsSubset",
    colors=vertex_colors[random_subset],
    size=0.05,
)

viewer.add_arrows(
    starts=points2[random_subset],
    ends=points[random_subset],
    name="Arrows",
    color=(0.01, 0.01, 0.01),
    width=0.01,
)

def whacky_transform(vertices, normals, t):
    # 1) swirl around Y: angle = t*2π * radius
    radii  = np.linalg.norm(vertices, axis=1)
    angles = radii * (t * 2*np.pi)
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

# bake whacky animation:
verts_animation = []
for t in np.linspace(0, 1, 50):
    temp_verts = whacky_transform(verts.copy(), normals, t)
    verts_animation.append(temp_verts)
verts_animation = np.stack(verts_animation)
# boomerang the animation:
verts_animation = np.concatenate([verts_animation, verts_animation[::-1]], axis=0)
viewer.add_animated_mesh(
    vertices=verts_animation,
    faces=faces,
    name="WhackyAnimation",
    framerate=24,
    vertex_colors=vertex_colors,
    position=(-2, 0, 0) # move to the left
)

viewer.hold()

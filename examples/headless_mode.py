import panopti
import trimesh

# Run in headless mode
viewer = panopti.connect(server_url="http://localhost:8080", viewer_id='client', headless=True)

mesh = trimesh.creation.icosphere(subdivisions=4)
verts, faces = mesh.vertices, mesh.faces
viewer.add_mesh(vertices=verts, faces=faces, name="icosphere")

viewer.screenshot("screenshot.png", resolution=(1024, 1024))
"""Import the actual Tripo export unchanged and render four neutral views."""
import bpy
import json
import math
from pathlib import Path
from mathutils import Vector

ROOT = Path(__file__).resolve().parents[1]
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=str(ROOT / 'assets/ink-hero-tpose.glb'))
meshes = [o for o in bpy.context.scene.objects if o.type == 'MESH']
points = [o.matrix_world @ Vector(c) for o in meshes for c in o.bound_box]
lo = Vector([min(p[i] for p in points) for i in range(3)])
hi = Vector([max(p[i] for p in points) for i in range(3)])
center = (lo + hi) / 2
size = max(hi - lo)
report = {'source': 'Tripo P2.0 export, no geometry edits',
          'asset_id': '38c66e6c-230a-439e-81bc-7ebee9b2221f',
          'meshes': len(meshes), 'vertices': sum(len(o.data.vertices) for o in meshes),
          'faces': sum(len(o.data.polygons) for o in meshes),
          'quads': sum(len(p.vertices) == 4 for o in meshes for p in o.data.polygons),
          'armatures': sum(o.type == 'ARMATURE' for o in bpy.context.scene.objects),
          'materials': len(bpy.data.materials), 'bounds_min': list(lo), 'bounds_max': list(hi),
          'rigging_validated': False}
scene = bpy.context.scene
scene.render.engine = 'CYCLES'
scene.cycles.samples = 16
scene.render.resolution_x = scene.render.resolution_y = 640
scene.render.resolution_percentage = 100
scene.world = bpy.data.worlds.new('ReviewWorld')
scene.world.use_nodes = True
scene.world.node_tree.nodes['Background'].inputs[0].default_value = (.7,.7,.7,1)
scene.world.node_tree.nodes['Background'].inputs[1].default_value = .7
scene.view_settings.view_transform = 'Standard'
scene.render.film_transparent = False
bpy.ops.object.camera_add()
camera = bpy.context.object
camera.data.type = 'ORTHO'
camera.data.ortho_scale = size * 1.18
scene.camera = camera
for angle, label in [(0,'front'),(90,'side'),(180,'back'),(270,'other-side')]:
    a = math.radians(angle)
    camera.location = center + Vector((math.sin(a)*size*3, -math.cos(a)*size*3, 0))
    camera.rotation_euler = (center-camera.location).to_track_quat('-Z','Y').to_euler()
    scene.render.filepath = str(ROOT / f'outputs/tripo-rebuild-{label}.png')
    bpy.ops.render.render(write_still=True)
bpy.ops.wm.save_as_mainfile(filepath=str(ROOT / 'outputs/tripo-rebuild.blend'))
(ROOT/'docs/logs/tripo-rebuild-structure.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report))

"""Import the actual Tripo export unchanged and render four neutral views."""
import bpy
import json
import math
import os
import numpy as np
from pathlib import Path
from mathutils import Vector

ROOT = Path(__file__).resolve().parents[1]
bpy.ops.wm.read_factory_settings(use_empty=True)
MODEL=os.environ.get('TRIPO_REVIEW_MODEL','assets/ink-hero-tpose.glb')
STEM=os.environ.get('TRIPO_REVIEW_STEM','tripo-rebuild')
ASSET_ID=os.environ.get('TRIPO_REVIEW_ID','38c66e6c-230a-439e-81bc-7ebee9b2221f')
baseline=[]
BASELINE=os.environ.get('TRIPO_REVIEW_BASELINE')
if BASELINE:
    bpy.ops.import_scene.gltf(filepath=str(ROOT/BASELINE))
    baseline=np.array([tuple(o.matrix_world@v.co) for o in bpy.context.scene.objects if o.type=='MESH' for v in o.data.vertices])
    bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=str(ROOT / MODEL))
meshes = [o for o in bpy.context.scene.objects if o.type == 'MESH']
points = [o.matrix_world @ Vector(c) for o in meshes for c in o.bound_box]
lo = Vector([min(p[i] for p in points) for i in range(3)])
hi = Vector([max(p[i] for p in points) for i in range(3)])
center = (lo + hi) / 2
size = max(hi - lo)
report = {'source': 'Tripo P2.0 export, no geometry edits',
          'asset_id': ASSET_ID, 'input': MODEL,
          'meshes': len(meshes), 'vertices': sum(len(o.data.vertices) for o in meshes),
          'faces': sum(len(o.data.polygons) for o in meshes),
          'quads': sum(len(p.vertices) == 4 for o in meshes for p in o.data.polygons),
          'armatures': sum(o.type == 'ARMATURE' for o in bpy.context.scene.objects),
          'materials': len(bpy.data.materials), 'bounds_min': list(lo), 'bounds_max': list(hi),
          'rigging_validated': False}
report['texture_images']=[{'name':im.name,'size':list(im.size)} for im in bpy.data.images if im.source=='FILE']
if BASELINE:
    current=np.array([tuple(o.matrix_world@v.co) for o in meshes for v in o.data.vertices])
    def max_nearest(a,b):
        return max(float(np.sqrt(((chunk[:,None,:]-b[None,:,:])**2).sum(2).min(1)).max()) for chunk in np.array_split(a,max(1,len(a)//128)))
    distance=max(max_nearest(current,baseline),max_nearest(baseline,current))
    report['baseline_model']=BASELINE
    report['geometry_surface_vertex_distance_max_m']=distance
    assert distance<1e-5, 'Texture export changed the model geometry'
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
    scene.render.filepath = str(ROOT / f'outputs/{STEM}-{label}.png')
    bpy.ops.render.render(write_still=True)
bpy.ops.wm.save_as_mainfile(filepath=str(ROOT / f'outputs/{STEM}.blend'))
(ROOT/f'docs/logs/{STEM}-structure.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report))

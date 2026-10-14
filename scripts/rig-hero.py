"""Blender 4.5: fit a simple deform rig to the original Tripo hero and bake Kimodo walk.

Run with Blender --background --factory-startup --python scripts/rig-hero.py.
The source GLB is never overwritten. This is an editable first-pass body rig.
"""
import bpy
import json
import math
import sys
import numpy as np
import hashlib
from pathlib import Path
from mathutils import Vector, Matrix

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'outputs'
OUT.mkdir(exist_ok=True)
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)
working_cache = ROOT / '.cache/hero-working.glb'
cache_hash = ROOT / '.cache/hero-working-source.sha256'
source_hash = hashlib.sha256((ROOT/'assets/ink-hero.glb').read_bytes()).hexdigest()
use_cache = working_cache.exists() and cache_hash.exists() and cache_hash.read_text().strip() == source_hash
bpy.ops.import_scene.gltf(filepath=str(working_cache if use_cache else ROOT / 'assets/ink-hero.glb'))
hero = next(o for o in bpy.context.scene.objects if o.type == 'MESH')
hero.name = 'InkHero'
bpy.context.view_layer.objects.active = hero
hero.select_set(True)
bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
original_vertices = 983284
# The million-vertex source is preserved on disk; the working mesh retains UVs.
if not use_cache:
    dec = hero.modifiers.new('Working mesh reduction', 'DECIMATE')
    dec.ratio = 0.045
    bpy.ops.object.modifier_apply(modifier=dec.name)
    bpy.ops.export_scene.gltf(filepath=str(working_cache), use_selection=True, export_animations=False)
    cache_hash.write_text(source_hash+'\n')
for p in hero.data.polygons:
    p.use_smooth = True
print('WORKING_MESH', original_vertices, len(hero.data.vertices), flush=True)

# Blender Z up, character front -Y. Positions measured from the GLB bounds.
# The head is deliberately one rigid deform region to protect the face/hood.
spec = {
    'Hips': ((0, .015, .34), (0, .015, .41), None),
    'Spine1': ((0, .015, .41), (0, .012, .48), 'Hips'),
    'Chest': ((0, .012, .48), (0, .01, .57), 'Spine1'),
    'Head': ((0, .01, .57), (0, .01, .92), 'Chest'),
}
for side, sign in [('Left', 1), ('Right', -1)]:
    spec.update({
        side+'Arm': ((sign*.115, .005, .535), (sign*.207, .005, .424), 'Chest'),
        side+'ForeArm': ((sign*.207, .005, .424), (sign*.263, .005, .349), side+'Arm'),
        side+'Hand': ((sign*.263, .005, .349), (sign*.275, .005, .303), side+'ForeArm'),
        side+'UpLeg': ((sign*.085, .015, .345), (sign*.117, .022, .211), 'Hips'),
        side+'Leg': ((sign*.117, .022, .211), (sign*.137, .032, .10), side+'UpLeg'),
        side+'Foot': ((sign*.137, .032, .10), (sign*.137, -.10, .052), side+'Leg'),
    })
rig_data = bpy.data.armatures.new('HeroRig')
rig = bpy.data.objects.new('HeroRig', rig_data)
bpy.context.collection.objects.link(rig)
bpy.context.view_layer.objects.active = rig
bpy.ops.object.mode_set(mode='EDIT')
for name, (head, tail, parent) in spec.items():
    b = rig_data.edit_bones.new(name)
    b.head, b.tail = head, tail
    if parent:
        b.parent = rig_data.edit_bones[parent]
bpy.ops.object.mode_set(mode='OBJECT')
rig.show_in_front = True
bpy.ops.object.select_all(action='DESELECT')
hero.select_set(True)
rig.select_set(True)
bpy.context.view_layer.objects.active = rig
# Tripo's overlapping clothing prevents bone-heat solving. Use explicit
# anatomical regions and normalized smooth segment-distance weights instead.
bpy.ops.object.parent_set(type='ARMATURE_NAME')
coords = np.array([v.co[:] for v in hero.data.vertices])
names = list(spec)
distances = []
for n in names:
    a, b, _ = spec[n]
    a, b = np.array(a), np.array(b)
    t = np.clip((coords-a) @ (b-a) / np.dot(b-a, b-a), 0, 1)
    distances.append(np.linalg.norm(coords-(a+t[:, None]*(b-a)), axis=1))
distances = np.array(distances).T
def ramp(value, low, high):
    t = min(1.0, max(0.0, (value-low)/(high-low)))
    return t*t*(3-2*t)

for v, co, ds in zip(hero.data.vertices, coords, distances):
    x, y, z = co
    side = 'Left' if x > 0 else 'Right'
    head = ramp(z, .555, .605)
    arm = ramp(abs(x), .13+max(0,.535-z)*.18, .19+max(0,.535-z)*.18)
    arm *= ramp(z, .245, .29) * (1-ramp(z, .535, .575))
    leg = (1-ramp(z, .30, .38)) * (1-arm)
    masks = {'Head': head, 'Hips': (1-head)*(1-arm),
             'Spine1': (1-head)*(1-arm)*(1-leg), 'Chest': (1-head)*(1-arm)*(1-leg)}
    for s, sign in [('Left', 1), ('Right', -1)]:
        lateral = ramp(sign*x, -.015, .015)
        for suffix in ('Arm', 'ForeArm', 'Hand'):
            masks[s+suffix] = (1-head)*arm*lateral
        for suffix in ('UpLeg', 'Leg', 'Foot'):
            masks[s+suffix] = (1-head)*leg*lateral
    ids = [i for i,n in enumerate(names) if masks.get(n,0) > 0]
    weights = np.array([masks[names[i]] for i in ids]) / np.maximum(ds[ids], .012)**4
    weights /= weights.sum()
    for idx, weight in zip(ids, weights):
        if weight > .001:
            hero.vertex_groups[names[idx]].add([v.index], float(weight), 'REPLACE')
unweighted = sum(not v.groups for v in hero.data.vertices)
assert unweighted == 0, f'Unweighted vertices: {unweighted}'

bpy.ops.import_anim.bvh(filepath=str(OUT / 'walk.bvh'), global_scale=.01,
                        axis_forward='-Z', axis_up='Y', frame_start=1,
                        use_fps_scale=False, update_scene_fps=True,
                        update_scene_duration=True)
source = bpy.context.object
source.name = 'KimodoSource'
source.hide_render = True
source.hide_set(True)
scene = bpy.context.scene
scene.frame_start, scene.frame_end = 1, 90
scene.render.fps = 30
scene.render.fps_base = 1
target_leg_length = sum((Vector(spec['Left'+n][1])-Vector(spec['Left'+n][0])).length
                        for n in ('UpLeg', 'Leg'))
source_leg_length = sum(source.data.bones[n].length for n in ('LeftLeg', 'LeftShin'))
scale = target_leg_length / source_leg_length
rest = {n: rig.data.bones[n].matrix_local.copy() for n in spec}
rest_rel = {n: (rest[p].inverted() @ rest[n] if p else rest[n])
            for n, (_, _, p) in spec.items()}
source_names = {n: n.replace('UpLeg', 'Leg') if 'UpLeg' in n
                else n.replace('Leg', 'Shin') if n.endswith('Leg') else n
                for n in spec}
foot_bottoms = []
for f in range(1, 91):
    scene.frame_set(f)
    desired = {}
    for n, (_, _, parent) in spec.items():
        # Source and target use the same world axes. Copy the posed world
        # orientation, then solve relative to the fitted A-pose rest bones.
        world = source.pose.bones[source_names[n]].matrix.to_quaternion().to_matrix().to_4x4()
        desired[n] = world
        relative = desired[parent].inverted() @ world if parent else world
        q = (rest_rel[n].to_quaternion().to_matrix().inverted()
             @ relative.to_3x3()).to_quaternion()
        pb = rig.pose.bones[n]
        pb.rotation_mode = 'QUATERNION'
        if f > 1:
            q.make_compatible(pb.rotation_quaternion)
        pb.rotation_quaternion = q
        pb.keyframe_insert('rotation_quaternion', frame=f)
    # Scale root bob/stride to the character. Keep horizontal travel in the
    # source action, and provide a centered preview using the rig translation.
    src_hip = source.pose.bones['Hips'].matrix.translation
    if f == 1:
        first_hip = src_hip.copy()
    rig.location = Vector(((src_hip.x-first_hip.x)*scale,
                           (src_hip.y-first_hip.y)*scale,
                           (src_hip.z-first_hip.z)*scale))
    rig.keyframe_insert('location', frame=f)
    bpy.context.view_layer.update()
    deps = bpy.context.evaluated_depsgraph_get()
    evaluated = hero.evaluated_get(deps)
    mesh = evaluated.to_mesh()
    foot_bottoms.append(min((evaluated.matrix_world @ v.co).z for v in mesh.vertices))
    evaluated.to_mesh_clear()
# One constant offset preserves original bob; do not stretch bones to ground.
ground_offset = -min(foot_bottoms)
for f in range(1, 91):
    scene.frame_set(f)
    rig.location.z -= foot_bottoms[f-1]
    rig.keyframe_insert('location', frame=f)
if rig.animation_data and rig.animation_data.action:
    rig.animation_data.action.name = 'Kimodo_Walk_3s'

# Neutral orthographic studio preview. Camera follows travel, preserving motion.
bpy.ops.object.camera_add(location=(1.35, -2.7, 1.18))
camera = bpy.context.object
camera.name = 'WalkPreviewCamera'
camera.data.type = 'ORTHO'
camera.data.ortho_scale = 1.32
scene.camera = camera
for f in range(1, 91):
    scene.frame_set(f)
    center = rig.location + Vector((0, 0, .49))
    camera.location = center + Vector((1.35, -2.7, .69))
    camera.rotation_euler = (center-camera.location).to_track_quat('-Z', 'Y').to_euler()
    camera.keyframe_insert('location', frame=f)
    camera.keyframe_insert('rotation_euler', frame=f)
bpy.ops.mesh.primitive_plane_add(size=200, location=(0, 0, -.002))
floor = bpy.context.object
floor.name = 'StudioFloor'
mat = bpy.data.materials.new('StudioFloor')
mat.diffuse_color = (.085, .11, .14, 1)
floor.data.materials.append(mat)
for pos, power, size in [((1, -2, 3), 350, 3), ((-2, -1, 2), 220, 3), ((0, 2, 2), 250, 2)]:
    bpy.ops.object.light_add(type='AREA', location=pos)
    light = bpy.context.object
    light.data.energy, light.data.shape, light.data.size = power, 'DISK', size
    light.rotation_euler = (Vector((0, 0, .5))-light.location).to_track_quat('-Z','Y').to_euler()
scene.world.color = (.20, .20, .20)
scene.render.engine = 'CYCLES'
scene.cycles.samples = 16
scene.cycles.use_denoising = True
cycles_prefs = bpy.context.preferences.addons['cycles'].preferences
cycles_prefs.compute_device_type = 'CUDA'
cycles_prefs.get_devices()
for device in cycles_prefs.devices:
    device.use = device.type == 'CUDA'
if any(d.type == 'CUDA' for d in cycles_prefs.devices):
    scene.cycles.device = 'GPU'
print('RENDER_DEVICES', [(d.name, d.type, d.use) for d in cycles_prefs.devices], flush=True)
scene.render.resolution_x = scene.render.resolution_y = 512
scene.render.resolution_percentage = 100
scene.view_settings.view_transform = 'Standard'
scene.view_settings.exposure = -.7
scene.render.image_settings.file_format = 'PNG'
scene.frame_set(1)
bpy.ops.wm.save_as_mainfile(filepath=str(OUT / 'hero-walk.blend'), compress=True)
bpy.ops.object.select_all(action='DESELECT')
hero.select_set(True)
rig.select_set(True)
bpy.context.view_layer.objects.active = rig
bpy.ops.export_scene.gltf(filepath=str(OUT / 'hero-walk.glb'), use_selection=True,
                          export_animations=True, export_frame_range=True,
                          export_force_sampling=True, export_animation_mode='SCENE')
report = {'blender': bpy.app.version_string, 'original_vertices': original_vertices,
          'working_vertices': len(hero.data.vertices), 'working_triangles': len(hero.data.polygons),
          'deform_bones': len(spec), 'unweighted_vertices': unweighted,
          'frames': 90, 'fps': 30, 'ground_offset_m': ground_offset,
          'root_motion_scale': scale, 'foot_min_before_ground_offset_m': min(foot_bottoms),
          'target_leg_length_m': target_leg_length, 'source_leg_length_m': source_leg_length,
          'weight_method': 'Anatomical regions + normalized segment-distance weights; rigid hood/face',
          'foot_min_range_m': max(foot_bottoms)-min(foot_bottoms),
          'grounding': 'Per-frame vertical root correction to lowest deformed vertex; no bone stretching',
          'source': 'assets/ink-hero.glb', 'motion': 'outputs/walk.bvh',
          'source_sha256': source_hash,
          'status': 'First-pass rig; requires rendered deformation review.'}
(ROOT/'docs/logs/hero-rig-check.json').write_text(json.dumps(report, indent=2)+'\n')
print(json.dumps(report, indent=2), flush=True)
render_frames = range(1, 91) if '--render-all' in sys.argv else (1, 16, 31, 46, 61, 76)
frame_dir = ROOT / '.cache/hero-frames'
frame_dir.mkdir(parents=True, exist_ok=True)
for f in render_frames:
    scene.frame_set(f)
    scene.render.filepath = str(frame_dir / f'{f:03d}.png')
    bpy.ops.render.render(write_still=True)

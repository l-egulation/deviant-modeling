"""Blender 4.5: fit a simple deform rig to the original Tripo hero and bake Kimodo walk.

Run with Blender --background --factory-startup --python scripts/rig-hero.py.
The source GLB is never overwritten. This is an editable first-pass body rig.
"""
import os
import bpy
import json
import math
import sys
import numpy as np
import hashlib
from pathlib import Path
from mathutils import Vector, Matrix, Quaternion
sys.path.insert(0, str(Path(__file__).resolve().parent))
from retarget import retarget_rotation
from hero_preview import boot_rotation, configure_preview
from hero_feet import plant_feet
from hero_accessories import refine_accessories
from hero_motion import pose_run_arms
from hero_timing import accelerate_run

ROOT = Path(__file__).resolve().parents[1]
MOTION = os.environ.get('HERO_MOTION', 'walk')
assert MOTION in ('walk', 'run')
LOG_STEM = 'hero' if MOTION == 'walk' else 'hero-run'
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
accessory_report=refine_accessories(hero) if MOTION == 'run' else {}

bpy.ops.import_anim.bvh(filepath=str(OUT / f'{MOTION}.bvh'), global_scale=.01,
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
source_reference = {n: source.data.bones[source_names[n]].matrix_local.to_3x3()
                    for n in spec}
# BVH bone roll includes arbitrary import geometry (hips can point down).
# Strip it before applying motion. Arms use a shared A-pose calibration per
# chain; this avoids adding a T-to-A offset a second time at elbow and wrist.
for side in ('Left', 'Right'):
    src_axis = source_reference[side+'Arm'].col[1].normalized()
    dst_axis = rest[side+'Arm'].to_3x3().col[1].normalized()
    a_pose = src_axis.rotation_difference(dst_axis).to_matrix()
    for suffix in ('Arm', 'ForeArm', 'Hand'):
        name = side+suffix
        correction=a_pose
        if MOTION == 'run':
            correction=source_reference[name].col[1].normalized().rotation_difference(rest[name].to_3x3().col[1].normalized()).to_matrix()
        source_reference[name] = correction @ source_reference[name]

def set_target_rotations(source_rotations, frame=None):
    desired = {}
    heading_correction=Matrix.Identity(3)
    for n, (_, _, parent) in spec.items():
        world = retarget_rotation(source_rotations[n], source_reference[n], rest[n].to_3x3())
        if MOTION == 'run' and frame is not None and n == 'Chest':
            yaw=(world@rest[n].to_3x3().inverted()).to_euler('XYZ').z
            heading_correction=Quaternion(Vector((0,0,1)),-.8*yaw-math.radians(8)).to_matrix()
            world=Quaternion(Vector((1,0,0)),math.radians(6)).to_matrix()@heading_correction@world
        if MOTION == 'run' and frame is not None and n == 'Head':
            # The hood and scarf form a connected shell. Keep their deformation
            # coherent rather than stretching the neck under an adult head nod.
            world=desired['Chest']@rest_rel[n].to_3x3()
        if MOTION == 'run' and frame is not None and n.endswith(('Arm','ForeArm','Hand')):
            # Give the hero's thick coat and large gloves a little clearance.
            angle=math.radians(-7 if n.startswith('Left') else 7)
            world=heading_correction@Quaternion(Vector((0,1,0)),angle).to_matrix()@world
        if n.endswith('Foot'):
            world = boot_rotation(world, rest[n].to_3x3())
        desired[n] = world
        relative = desired[parent].inverted() @ world if parent else world
        q = (rest_rel[n].to_3x3().inverted() @ relative).to_quaternion()
        pb = rig.pose.bones[n]
        pb.rotation_mode = 'QUATERNION'
        q.make_compatible(pb.rotation_quaternion)
        pb.rotation_quaternion = q
        if frame is not None:
            pb.keyframe_insert('rotation_quaternion', frame=frame)

# A calibrated neutral source must reproduce the unposed mesh, vertex for
# vertex. The previous absolute-frame copy fails this regression badly.
set_target_rotations(source_reference)
bpy.context.view_layer.update()
eval_hero = hero.evaluated_get(bpy.context.evaluated_depsgraph_get())
neutral_mesh = eval_hero.to_mesh()
neutral_error = max((v.co-hero.data.vertices[v.index].co).length for v in neutral_mesh.vertices)
eval_hero.to_mesh_clear()
assert neutral_error < 1e-5, f'Bind pose changed the mesh: {neutral_error} m'
foot_bottoms = []
for f in range(1, 91):
    scene.frame_set(f)
    set_target_rotations({n: source.pose.bones[source_names[n]].matrix.to_quaternion().to_matrix()
                          for n in spec}, frame=f)
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
# Ground the fitted legs using root translation, never bone or mesh scaling.
ground_offset = -min(foot_bottoms)
for f in range(1, 91):
    scene.frame_set(f)
    rig.location.z -= foot_bottoms[f-1]
    rig.keyframe_insert('location', frame=f)
if rig.animation_data and rig.animation_data.action:
    rig.animation_data.action.name = f'Kimodo_{MOTION.title()}_3s'
arm_motion_report=pose_run_arms(scene,rig) if MOTION == 'run' else {}
contact_report = plant_feet(scene, rig, hero, source, OUT/f'{MOTION}.npz', allow_flight=MOTION == 'run')
if MOTION == 'run':
    timing_report=accelerate_run(scene,rig,hero)
    (ROOT/'docs/logs/hero-run-timing.json').write_text(json.dumps(timing_report,indent=2)+'\n')

# Neutral orthographic studio preview. Camera follows travel, preserving motion.
bpy.ops.object.camera_add(location=(1.35, -2.7, .70))
camera = bpy.context.object
camera.name = 'WalkPreviewCamera'
camera.data.type = 'ORTHO'
camera.data.ortho_scale = 1.32
scene.camera = camera
for f in range(1, 91):
    scene.frame_set(f)
    # Follow horizontal travel only; pelvis bob must not shake the floor.
    center = Vector((rig.location.x, rig.location.y, .49))
    camera.location = center + Vector((1.35, -2.7, .18))
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
configure_preview(scene, rig, camera)
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
bpy.ops.wm.save_as_mainfile(filepath=str(OUT / f'hero-{MOTION}.blend'), compress=True)
bpy.ops.object.select_all(action='DESELECT')
hero.select_set(True)
rig.select_set(True)
bpy.context.view_layer.objects.active = rig
scene.frame_end=91 if 'loop_displacement' in rig else 90
bpy.ops.export_scene.gltf(filepath=str(OUT / f'hero-{MOTION}.glb'), use_selection=True,
                          export_animations=True, export_frame_range=True,
                          export_force_sampling=True, export_animation_mode='SCENE',
                          export_anim_slide_to_zero=MOTION == 'run')
scene.frame_end=90
report = {'blender': bpy.app.version_string, 'original_vertices': original_vertices,
          'working_vertices': len(hero.data.vertices), 'working_triangles': len(hero.data.polygons),
          'deform_bones': len(spec), 'unweighted_vertices': unweighted,
          'frames': 90, 'fps': 30, 'ground_offset_m': ground_offset,
          'root_motion_scale': scale, 'foot_min_before_ground_offset_m': min(foot_bottoms),
          'target_leg_length_m': target_leg_length, 'source_leg_length_m': source_leg_length,
          'weight_method': 'Anatomical segment weights with rigid hood/face and rigid boot soles',
          'foot_min_range_m': max(foot_bottoms)-min(foot_bottoms),
          'grounding': 'Source contact anchors, fixed-length leg IK, smooth reachable pelvis height',
          'source': 'assets/ink-hero.glb', 'motion': f'outputs/{MOTION}.bvh',
          'source_sha256': source_hash,
          'neutral_pose_max_vertex_error_m': neutral_error,
          'contact_polish': contact_report,
          'run_accessory_rigid_groups': accessory_report,
          'run_head_follows_chest': MOTION == 'run',
          'run_arm_motion':arm_motion_report,
          'retarget_method': 'Source bind rotation removed; shared arm A-pose calibration; target rest axes retained',
          'status': 'First-pass rig; requires rendered deformation review.'}
(ROOT/f'docs/logs/{LOG_STEM}-rig-check.json').write_text(json.dumps(report, indent=2)+'\n')
print(json.dumps(report, indent=2), flush=True)
render_frames = range(1, 91) if '--render-all' in sys.argv else (1, 16, 31, 46, 61, 76)
frame_dir = ROOT / ('.cache/hero-frames' if MOTION == 'walk' else '.cache/hero-run-frames')
frame_dir.mkdir(parents=True, exist_ok=True)
for f in render_frames:
    scene.frame_set(f)
    scene.render.filepath = str(frame_dir / f'{f:03d}.png')
    bpy.ops.render.render(write_still=True)

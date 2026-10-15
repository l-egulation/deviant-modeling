"""Fix the saved preview camera without rebuilding or altering the hero motion."""
import bpy
import json
import numpy as np
from pathlib import Path
from mathutils import Vector
from bpy_extras.object_utils import world_to_camera_view

ROOT = Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(ROOT/'outputs/hero-walk.blend'))
scene = bpy.context.scene
rig, camera = bpy.data.objects['HeroRig'], scene.camera
floor = bpy.data.objects['StudioFloor']

def snapshot():
    poses, heights, floor_heights, floor_matrices = [], [], [], []
    for f in range(1,91):
        scene.frame_set(f)
        poses.append([*rig.matrix_world[:], *[row for b in rig.pose.bones for row in b.matrix]])
        heights.append(camera.location.z)
        floor_matrices.append(np.array(floor.matrix_world))
        ground = Vector((rig.location.x,rig.location.y,0))
        floor_heights.append(world_to_camera_view(scene,camera,ground).y)
    return np.array(poses), np.array(heights), np.array(floor_heights), np.array(floor_matrices)

before, z_before, screen_before, ground_before = snapshot()
camera.animation_data_clear()
offset = Vector((1.35,-2.7,.18))
for f in range(1,91):
    scene.frame_set(f)
    center = Vector((rig.location.x,rig.location.y,.49))
    camera.location = center+offset
    camera.rotation_euler = (-offset).to_track_quat('-Z','Y').to_euler()
    camera.keyframe_insert('location',frame=f)
    camera.keyframe_insert('rotation_euler',frame=f)
after, z_after, screen_after, ground_after = snapshot()
assert np.array_equal(before,after), 'Character pose or root motion changed'
assert np.array_equal(ground_before,ground_after), 'Floor transform changed'
assert np.ptp(z_after)<1e-7
assert np.ptp(screen_after)<1e-6
scene.frame_set(1)
bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'outputs/hero-walk.blend'),compress=True)
report = {'status':'PASS','frames_checked':90,
          'camera_vertical_travel_before_m':float(np.ptp(z_before)),
          'camera_vertical_travel_after_m':float(np.ptp(z_after)),
          'ground_screen_vertical_travel_before_pixels':float(np.ptp(screen_before)*512),
          'ground_screen_vertical_travel_after_pixels':float(np.ptp(screen_after)*512),
          'character_pose_and_root_motion_unchanged':True,'floor_transform_unchanged':True,
          'fix':'Fixed camera height and angle; horizontal tracking only. No grounding or rig changes.'}
(ROOT/'docs/logs/hero-camera-check.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report,indent=2),flush=True)

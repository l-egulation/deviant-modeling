"""Validate and rebuild a linear preview track without modifying the hero."""
import bpy,json,sys,numpy as np
from pathlib import Path
from mathutils import Vector
from bpy_extras.object_utils import world_to_camera_view
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
from hero_preview import configure_preview
bpy.ops.wm.open_mainfile(filepath=str(ROOT/'outputs/hero-walk.blend'))
scene=bpy.context.scene;rig=bpy.data.objects['HeroRig'];camera=scene.camera
floor=bpy.data.objects['StudioFloor'];lights=[o for o in scene.objects if o.type=='LIGHT']
def snapshot():
 poses=[];positions=[];rotations=[];ground=[];screens=[];lighting=[]
 for f in range(1,91):
  scene.frame_set(f)
  poses.append([*rig.matrix_world[:],*[row for b in rig.pose.bones for row in b.matrix]])
  positions.append(camera.matrix_world.translation[:]);rotations.append(camera.rotation_euler[:]);ground.append(np.array(floor.matrix_world))
  screens.append([world_to_camera_view(scene,camera,Vector(p))[:2] for p in ((0,0,0),(1,0,0),(0,-1,0))])
  lighting.append([(o.matrix_world.translation-camera.matrix_world.translation)[:] for o in lights])
 return [np.array(v) for v in (poses,positions,rotations,ground,screens,lighting)]
before=snapshot();configure_preview(scene,rig,camera);after=snapshot()
assert np.array_equal(before[0],after[0]),'Character changed'
assert np.array_equal(before[3],after[3]),'Floor changed'
residual=after[1]-np.linspace(after[1][0],after[1][-1],90)
screen_residual=after[4]-np.linspace(after[4][0],after[4][-1],90)
assert np.abs(residual).max()<1e-6
assert np.ptp(after[2],axis=0).max()<1e-7
assert np.ptp(after[5],axis=0).max()<1e-6
assert np.abs(screen_residual).max()*512<.001
scene.frame_set(1);bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'outputs/hero-walk.blend'),compress=True)
report={'status':'PASS','frames_checked':90,'camera_constant_velocity_residual_max_m':float(np.abs(residual).max()),'fixed_world_ground_projection_residual_max_pixels':float(np.abs(screen_residual).max()*512),'camera_rotation_range_radians':np.ptp(after[2],axis=0).tolist(),'studio_light_relative_position_range_max_m':float(np.ptp(after[5],axis=0).max()),'character_pose_and_root_motion_unchanged':True,'floor_transform_unchanged':True,'method':'Fixed WORLD ground points must project along straight constant-speed paths; not pelvis-attached ground samples.'}
(ROOT/'docs/logs/hero-camera-check.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))

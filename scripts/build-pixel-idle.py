"""Small authored breathing idle for art comparison, not generated/mocap motion."""
import bpy,math,json
import numpy as np
from pathlib import Path
from mathutils import Vector,Matrix
R=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(R/'outputs/tripo-pixel-rig.blend'))
s=bpy.context.scene;rig=bpy.data.objects['TripoPixel_Rig'];h=bpy.data.objects['TripoPixel_Character']
rig.animation_data_clear();rig.location=(0,0,0)
for pb in rig.pose.bones:pb.rotation_mode='QUATERNION';pb.rotation_quaternion=(1,0,0,0);pb.location=(0,0,0);pb.scale=(1,1,1)
s.frame_start=1;s.frame_end=90;s.render.fps=30
rest={b.name:b.matrix_local.copy() for b in rig.data.bones}
foot_positions=[];max_length_error=0
for f in range(1,91):
 s.frame_set(f);phase=2*math.pi*(f-1)/90;breath=math.sin(phase)
 for pb in rig.pose.bones:pb.rotation_quaternion=(1,0,0,0)
 for name,angle in [('Spine',.7*breath),('Chest',1.2*breath),('Neck',-.8*breath)]:
  rig.pose.bones[name].rotation_quaternion=Matrix.Rotation(math.radians(angle),4,'X').to_quaternion()
 bpy.context.view_layer.update()
 for side,sign in [('L',1),('R',-1)]:
  for name,direction in [('UpperArm',(.18*sign,-.07-.015*breath,-1)),('Forearm',(.04*sign,-.33-.025*breath,-1)),('Hand',(.03*sign,-.3,-1))]:
   pb=rig.pose.bones[name+'.'+side];axis=rest[pb.name].to_3x3().col[1].normalized();q=axis.rotation_difference(Vector(direction).normalized())@rest[pb.name].to_quaternion()
   pb.matrix=Matrix.LocRotScale(pb.head.copy(),q,Vector((1,1,1)));bpy.context.view_layer.update()
 for pb in rig.pose.bones:
  pb.keyframe_insert('rotation_quaternion',frame=f,group=pb.name)
  max_length_error=max(max_length_error,abs((pb.tail-pb.head).length-rig.data.bones[pb.name].length))
 foot_positions.append([list(rig.pose.bones['Foot.'+side].head) for side in ['L','R']])
feet=np.array(foot_positions);drift=float(np.abs(feet-feet[0]).max());assert drift<1e-7 and max_length_error<1e-6
cam=s.camera;cam.animation_data_clear();cam.data.type='ORTHO';cam.data.ortho_scale=1.36
center=Vector((.075,0,.51));offset=Vector((math.cos(math.radians(30)),-math.sin(math.radians(30)),0))*3
cam.location=center+offset;cam.rotation_euler=(-offset).to_track_quat('-Z','Y').to_euler()
s.render.resolution_x=s.render.resolution_y=384;s.cycles.samples=8
s.frame_set(1);bpy.ops.wm.save_as_mainfile(filepath=str(R/'outputs/pixel-idle.blend'),compress=True)
s.render.filepath=str(R/'outputs/pixel-idle-pose.png');bpy.ops.render.render(write_still=True)
(R/'docs/logs/pixel-idle.json').write_text(json.dumps({'motion':'authored breathing idle, not Kimodo or Mixamo','frames':90,'fps':30,'feet_max_drift_m':drift,'bone_length_error_m':max_length_error,'geometry_changed':False,'weapon_added':False},indent=2))

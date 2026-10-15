import bpy,json,math,numpy as np
from pathlib import Path
from mathutils import Vector
r=Path.cwd();bpy.ops.wm.open_mainfile(filepath=str(r/'outputs/tripo-run.blend'))
s=bpy.context.scene;rig=bpy.data.objects['TripoRunRig'];src=bpy.data.objects['KimodoSource'];rows=[]
for f in range(1,91):
 s.frame_set(f)
 def lean(v):return math.degrees(math.atan2(-v.y,v.z))
 a=lean(src.pose.bones['Neck1'].head-src.pose.bones['Hips'].head)
 b=lean(rig.pose.bones['Head'].head-rig.pose.bones['Hips'].head)
 head=rig.pose.bones['Head'];v=head.matrix.to_3x3()@head.bone.matrix_local.to_3x3().inverted()@Vector((0,-1,0))
 rows.append([a,b,math.degrees(math.atan2(-v.z,-v.y))])
report={'source_hips_to_neck_lean_mean':float(np.array(rows)[:,0].mean()),'target_hips_to_head_base_lean_mean':float(np.array(rows)[:,1].mean()),'target_head_forward_downward_angle_mean':float(np.array(rows)[:,2].mean()),'sample_frame16':rows[15], 'source_leg_length':sum(src.data.bones[n].length for n in ['LeftLeg','LeftShin']),'target_leg_length':sum(rig.data.bones[n].length for n in ['LeftUpLeg','LeftLeg'])}
(r/'docs/logs/kimodo-retarget-audit.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report))

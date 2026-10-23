"""Canonical world-space proxy of untouched Mixamo FBX, retaining source timing."""
import bpy,numpy as np,json,hashlib
from mathutils import Vector
def load_source(R):
 s=bpy.context.scene;before=set(s.objects)
 path=R/'assets/mixamo-running.fbx';bpy.ops.import_scene.fbx(filepath=str(path))
 added=[o for o in s.objects if o not in before];original=next(o for o in added if o.type=='ARMATURE')
 for o in added:o.hide_render=True;o.hide_set(True)
 def bone(n):return next(b for b in original.data.bones if b.name.endswith(n))
 forward=sum((original.matrix_world.to_3x3()@(bone(side+'ToeBase').head_local-bone(side+'Foot').head_local) for side in ['Left','Right']),Vector())
 forward.z=0;forward.normalize();alignment=forward.rotation_difference(Vector((0,-1,0))).to_matrix().to_4x4()
 mapping={'Hips':'Hips','Spine1':'Spine','Spine2':'Spine1','Chest':'Spine2','Neck1':'Neck','Head':'Head'}
 for side in ['Left','Right']:
  for a,b in [('Shoulder','Shoulder'),('Arm','Arm'),('ForeArm','ForeArm'),('Hand','Hand'),('Leg','UpLeg'),('Shin','Leg'),('Foot','Foot'),('ToeBase','ToeBase')]:mapping[side+a]=side+b
 def norm(m):
  r=m.to_quaternion().to_matrix().to_4x4();r.translation=m.translation;return r
 rest={n:norm(alignment@original.matrix_world@bone(m).matrix_local) for n,m in mapping.items()}
 # FBX local Y is not necessarily the anatomical joint direction (arms differ
 # by 90 degrees here). Express the same rotations in anatomical rest axes.
 children={'Hips':'Spine','Spine1':'Spine1','Spine2':'Spine2','Chest':'Neck','Neck1':'Head'}
 for side in ['Left','Right']:
  for n,c in [('Shoulder','Arm'),('Arm','ForeArm'),('ForeArm','Hand'),('Hand','HandMiddle1'),('Leg','Leg'),('Shin','Foot'),('Foot','ToeBase')]:children[side+n]=side+c
 basis={};lengths={}
 for n,m in mapping.items():
  b=bone(m);child=bone(children[n]) if n in children else (b.children[0] if b.children else None)
  direction=(alignment@original.matrix_world@child.head_local-rest[n].translation) if child else (alignment@original.matrix_world).to_3x3()@(b.tail_local-b.head_local)
  lengths[n]=direction.length
  rot=rest[n].to_3x3();fit=rot.col[1].rotation_difference(direction.normalized()).to_matrix()@rot
  basis[n]=rot.inverted()@fit;rest[n]=fit.to_4x4();rest[n].translation=alignment@original.matrix_world@b.head_local
 start,end=map(round,original.animation_data.action.frame_range);count=end-start+1
 samples=[]
 for f in range(start,end+1):
  s.frame_set(f);bpy.context.view_layer.update()
  row={}
  for n,m in mapping.items():
   matrix=norm(alignment@original.matrix_world@original.pose.bones[bone(m).name].matrix)
   canonical=(matrix.to_3x3()@basis[n]).to_4x4();canonical.translation=matrix.translation;row[n]=canonical
  samples.append(row)
 step=(samples[-1]['Hips'].translation-samples[0]['Hips'].translation)*(count/(count-1));step.z=0
 data=bpy.data.armatures.new('Mixamo canonical source');proxy=bpy.data.objects.new('Motion_Raw_Source',data);s.collection.objects.link(proxy)
 bpy.context.view_layer.objects.active=proxy;proxy.select_set(True);bpy.ops.object.mode_set(mode='EDIT')
 for n,m in mapping.items():
  b=data.edit_bones.new(n);b.length=lengths[n];b.matrix=rest[n]
 bpy.ops.object.mode_set(mode='OBJECT')
 for n in mapping:
  actual=proxy.data.bones[n].matrix_local.to_3x3().col[1]
  assert actual.normalized().dot(rest[n].to_3x3().col[1].normalized())>.99999,'Canonical rest axis lost: '+n
 all_positions=[]
 for i in range(90):
  s.frame_set(i+1);lap,phase=divmod(i,count);row={}
  for n in mapping:
   m=samples[phase][n].copy();m.translation+=step*lap;b=proxy.pose.bones[n];b.rotation_mode='QUATERNION';b.matrix=m
   b.keyframe_insert('location',frame=i+1);b.keyframe_insert('rotation_quaternion',frame=i+1);row[n]=list(m.translation)
  all_positions.append(row)
 feet=np.array([[r[side+'Foot'] for side in ['Left','Right']] for r in all_positions]);toes=np.array([[r[side+'ToeBase'] for side in ['Left','Right']] for r in all_positions])
 contact=(feet[:,:,2]<feet[:,:,2].min(0)+.025)|(toes[:,:,2]<toes[:,:,2].min(0)+.025)
 flags=np.repeat(contact,3,axis=1).astype(float)
 proxy.hide_render=True;proxy.hide_set(True)
 (R/'docs/logs/pixel-run-source.json').write_text(json.dumps({'kind':'Mixamo','source':'assets/mixamo-running.fbx','sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'source_cycle_frames':count,'frames':90,'fps':30,'source_timing_modified':False,'rotation_keys_modified':False,'note':'Original cycle repeated; canonical coordinate conversion only','joints':all_positions},indent=2))
 return proxy,{'foot_contacts':flags}

"""Retarget approved Mixamo onto the short rig. No joint translation/scale transfer."""
import bpy,math,json,sys
import numpy as np
from pathlib import Path
from mathutils import Vector,Matrix
R=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(R/'scripts'))
from pixel_mixamo_source import load_source
bpy.ops.wm.open_mainfile(filepath=str(R/'outputs/tripo-pixel-rig.blend'))
s=bpy.context.scene;rig=bpy.data.objects['TripoPixel_Rig'];hero=bpy.data.objects['TripoPixel_Character']
rig.animation_data_clear();rig.location=(0,0,0)
for pb in rig.pose.bones:pb.rotation_mode='QUATERNION';pb.rotation_quaternion=(1,0,0,0);pb.location=(0,0,0);pb.scale=(1,1,1)
src,data=load_source(R)
s.frame_start=1;s.frame_end=90;s.render.fps=30
mapping={'Hips':'Hips','Spine':'Spine1','Chest':'Chest','Neck':'Neck1','Head':'Head'}
for side,word in [('L','Left'),('R','Right')]:
 for target,source in [('Clavicle','Shoulder'),('UpperArm','Arm'),('Forearm','ForeArm'),('Hand','Hand'),('Thigh','Leg'),('Shin','Shin'),('Foot','Foot'),('Toe','ToeBase')]:mapping[target+'.'+side]=word+source
rest={b.name:b.matrix_local.copy() for b in rig.data.bones};desired={};ref={}
for n,m in mapping.items():
 sr=src.data.bones[m].matrix_local.to_3x3();tr=rest[n].to_3x3();correction=Matrix.Identity(3)
 if n.startswith(('UpperArm.','Forearm.','Hand.','Thigh.','Shin.','Foot.','Toe.')):correction=tr.col[1].rotation_difference(sr.col[1]).to_matrix()
 ref[n]=sr.inverted()@correction@tr
scale=np.mean([sum(rig.data.bones[n+'.'+side].length for n in ['Thigh','Shin'])/sum(src.data.bones[word+n].length for n in ['Leg','Shin']) for side,word in [('L','Left'),('R','Right')]])
contacts=np.stack([data['foot_contacts'][:,:3].max(1)>.5,data['foot_contacts'][:,3:].max(1)>.5],axis=1)
p=np.array([v.co[:] for v in hero.data.vertices]);boot={}
for side in ['L','R']:
 group=hero.vertex_groups['Region_Leg.'+side].index
 ids=[v.index for v in hero.data.vertices if v.co.z<.075 and any(g.group==group for g in v.groups)]
 boot[side]=p[ids]-np.array(rest['Foot.'+side].translation)
def assign(n,world):
 pb=rig.pose.bones[n];parent=pb.parent
 local=parent.matrix.to_3x3().inverted()@world if parent else world
 bind=rest[parent.name].to_3x3().inverted()@rest[n].to_3x3() if parent else rest[n].to_3x3()
 q=(bind.inverted()@local).to_quaternion();q.make_compatible(pb.rotation_quaternion);pb.rotation_quaternion=q
 bpy.context.view_layer.update()
rawposes=[];roots=[];targets=[];sourceheads=[]
for f in range(1,91):
 s.frame_set(f);bpy.context.view_layer.update()
 poses={n:src.pose.bones[m].matrix.to_3x3().normalized()@ref[n] for n,m in mapping.items()}
 rawposes.append(poses);roots.append(src.pose.bones['Hips'].head.copy());sourceheads.append([src.pose.bones[w+'Foot'].head.copy() for w in ['Left','Right']])
roots=np.array(roots);sourceheads=np.array(sourceheads);first=roots[0].copy()
rootpositions=(roots-first)*scale
# Foot world targets preserve the source stride and fitted hip spacing, with rigid sole height.
foot_targets=np.zeros((90,2,3));clearance=np.zeros((90,2))
for j,(side,word) in enumerate([('L','Left'),('R','Right')]):
 ankle=sourceheads[:,j];baseline=np.median(ankle[contacts[:,j],2]) if contacts[:,j].any() else ankle[:,2].min()
 clearance[:,j]=np.maximum(0,ankle[:,2]-baseline)*scale
 for f in range(90):
  t=(ankle[f]-first)*scale+np.array(rest['Hips'].translation)
  t[0]+=(rest['Thigh.'+side].translation.x-rest['Hips'].translation.x)-(src.data.bones[word+'Leg'].head_local.x-src.data.bones['Hips'].head_local.x)*scale
  delta=rawposes[f]['Foot.'+side]@rest['Foot.'+side].to_3x3().inverted()
  sole=boot[side]@np.array(delta).T
  t[2]=-sole[:,2].min()+(0 if contacts[f,j] else clearance[f,j]);foot_targets[f,j]=t
 # Anchor each support phase in world XY; soften entering/leaving anchors over three frames.
 original=foot_targets[:,j].copy();i=0
 while i<90:
  if not contacts[i,j]:i+=1;continue
  end=i
  while end+1<90 and contacts[end+1,j]:end+=1
  anchor=np.median(original[i:end+1,:2],axis=0);foot_targets[i:end+1,j,:2]=anchor
  for edge,direction in [(i,-1),(end,1)]:
   for step in range(1,4):
    k=edge+direction*step
    if 0<=k<90 and not contacts[k,j]:foot_targets[k,j,:2]+=(anchor-original[edge,:2])*(4-step)/4
  i=end+1
joint_frames=[];errors=[];bone_error=0;edge_peak=0;penetration=[]
edges=np.array([e.vertices[:] for e in hero.data.edges]);length=np.linalg.norm(p[edges[:,0]]-p[edges[:,1]],axis=1);valid=length>1e-4
for f in range(90):
 s.frame_set(f+1);rig.location=Vector(rootpositions[f]);bpy.context.view_layer.update()
 for n in mapping:assign(n,rawposes[f][n])
 # Lower the pelvis only when a planted target would otherwise require stretching a leg.
 dz=0.
 for j,side in enumerate(['L','R']):
  if not contacts[f,j]:continue
  hip=np.array(rig.pose.bones['Thigh.'+side].head+rig.location);t=foot_targets[f,j]
  L=sum(rig.data.bones[n+'.'+side].length for n in ['Thigh','Shin'])*.998
  horizontal=np.linalg.norm((t-hip)[:2]);limit=t[2]+math.sqrt(max(.00001,L*L-horizontal*horizontal))
  dz=min(dz,limit-hip[2])
 rig.location.z+=dz;bpy.context.view_layer.update()
 for j,side in enumerate(['L','R']):
  thigh=rig.pose.bones['Thigh.'+side];shin=rig.pose.bones['Shin.'+side];hip=thigh.head.copy();knee=shin.head.copy()
  target=Vector(foot_targets[f,j])-rig.location;direction=target-hip;distance=direction.length
  l1=rig.data.bones[thigh.name].length;l2=rig.data.bones[shin.name].length
  distance=max(abs(l1-l2)+1e-5,min(distance,(l1+l2)*.999));direction.normalize()
  bend=knee-hip-direction*(knee-hip).dot(direction)
  if bend.length<1e-5:bend=Vector((0,-1,0))-direction*Vector((0,-1,0)).dot(direction)
  bend.normalize();a=(l1*l1-l2*l2+distance*distance)/(2*distance);height=math.sqrt(max(0,l1*l1-a*a))
  goal_knee=hip+direction*a+bend*height;goal_ankle=hip+direction*distance
  world=thigh.matrix.to_3x3();assign(thigh.name,world.col[1].rotation_difference(goal_knee-hip).to_matrix()@world)
  world=shin.matrix.to_3x3();assign(shin.name,world.col[1].rotation_difference(goal_ankle-shin.head).to_matrix()@world)
  assign('Foot.'+side,rawposes[f]['Foot.'+side]);assign('Toe.'+side,rawposes[f]['Toe.'+side])
  errors.append(float((rig.pose.bones['Foot.'+side].head+rig.location-Vector(foot_targets[f,j])).length))
 for pb in rig.pose.bones:
  pb.keyframe_insert('rotation_quaternion',frame=f+1,group=pb.name)
  bone_error=max(bone_error,abs((pb.tail-pb.head).length-pb.bone.length));assert pb.location.length<1e-7 and max(abs(v-1) for v in pb.scale)<1e-7
 rig.keyframe_insert('location',frame=f+1)
 q=np.array([v.co[:] for v in hero.evaluated_get(bpy.context.evaluated_depsgraph_get()).data.vertices]);edge_peak=max(edge_peak,float((np.linalg.norm(q[edges[:,0]]-q[edges[:,1]],axis=1)[valid]/length[valid]).max()))
 penetration.append(float(q[:,2].min()+rig.location.z))
 joint_frames.append({n:(pb.head+rig.location)[:] for n,pb in rig.pose.bones.items()})
# Fixed camera height/orientation, linear horizontal travel only; no pelvis-bob tracking.
cam=s.camera;cam.animation_data_clear();cam.data.ortho_scale=1.25
for f in [1,90]:
 s.frame_set(f);center=Vector((.075+rig.location.x,rig.location.y,.49));cam.location=center+Vector((2.7,-1.4,0));cam.rotation_euler=(center-cam.location).to_track_quat('-Z','Y').to_euler();cam.keyframe_insert('location',frame=f)
for layer in cam.animation_data.action.layers:
 for strip in layer.strips:
  for bag in strip.channelbags:
   for curve in bag.fcurves:
    for k in curve.keyframe_points:k.interpolation='LINEAR'
s.render.resolution_x=s.render.resolution_y=384;s.cycles.samples=8
s.frame_set(1);bpy.ops.wm.save_as_mainfile(filepath=str(R/'outputs/pixel-run.blend'),compress=True)
report={'source':'assets/mixamo-running.fbx','frames':90,'scale_for_root_and_stride':float(scale),'bones':len(rig.data.bones),'bone_length_error_m':bone_error,'max_ankle_target_error_m':max(errors),'max_edge_stretch':edge_peak,'lowest_vertex_world_z_m':min(penetration),'source_rotations_changed':'Fixed-length leg contact IK only; arm/torso rotations transferred','mapping':mapping,'cloth_applied':False,'joints':joint_frames}
(R/'docs/logs/pixel-run-retarget.json').write_text(json.dumps(report,indent=2));print(json.dumps({k:v for k,v in report.items() if k!='joints'}),flush=True)
for f in [10,25,40,55]:
 s.frame_set(f);s.render.filepath=str(R/f'outputs/pixel-run-pose-{f}.png');bpy.ops.render.render(write_still=True)

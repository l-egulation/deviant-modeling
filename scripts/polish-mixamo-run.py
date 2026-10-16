"""User-approved elbow opening and periodic root-height stabilization; run after apply-mixamo-run.py."""
import bpy,json,math,numpy as np
from pathlib import Path
from mathutils import Quaternion
R=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(R/'outputs/hero-mixamo-run.blend'))
s=bpy.context.scene;r=bpy.data.objects['TripoRunRig'];h=bpy.data.objects['TripoHero']
assert not r.get('user_elbow_polish'), 'Rebuild with apply-mixamo-run.py first'
rest={b.name:b.matrix_local.copy() for b in r.data.bones};parents={b.name:b.parent.name if b.parent else None for b in r.data.bones}
rel={n:rest[p].inverted()@rest[n] if p else rest[n] for n,p in parents.items()}
roots=[];rotations=[];before=[];after=[];legs=[]
for f in range(1,91):
 s.frame_set(f);roots.append(r.location[:]);world={b.name:b.matrix.to_3x3().normalized() for b in r.pose.bones}
 for side in ('Left','Right'):
  a=world[side+'Arm'].col[1].normalized();b=world[side+'ForeArm'].col[1].normalized();bend=a.angle(b);interior=180-math.degrees(bend);wanted=120+10*math.tanh((interior-100)/25)
  delta=Quaternion(a.cross(b).normalized(),math.radians(180-wanted)-bend).to_matrix()
  for part in ('ForeArm','Hand'):world[side+part]=delta@world[side+part]
  before.append(interior);after.append(wanted)
 rotations.append(world)
 legs.append({side:[(r.matrix_world@r.pose.bones[side+part].head).copy() for part in ('UpLeg','Leg','Foot')] for side in ('Left','Right')})
roots=np.array(roots);period=22;t=np.arange(period)*2*np.pi/period
X=np.column_stack([np.ones(period)]+[fn(k*t) for k in (1,2,3) for fn in (np.cos,np.sin)])
fit=X@np.linalg.lstsq(X,roots[:period,2],rcond=None)[0];height=fit[np.arange(90)%period]
# Keep the hip below its original trajectory so fixed-length legs can retain
# the original world-space ankle targets while absorbing the height correction.
height-=max(height-roots[:,2])+.002
r.animation_data_clear()
# Spread the elbow transition across its outer fold without moving rest vertices.
for v in h.data.vertices:
 x,y,z=v.co;ax=abs(x)
 if .17<ax<.30 and .48<z<.61:
  side='Left' if x>=0 else 'Right';g={h.vertex_groups[a.group].name:a.weight for a in v.groups};total=sum(g.get(side+p,0) for p in ('Arm','ForeArm'))
  if total>.99:
   q=float(np.clip((ax-.17)/.13,0,1));q=q*q*(3-2*q)
   h.vertex_groups[side+'Arm'].add([v.index],total*(1-q),'REPLACE');h.vertex_groups[side+'ForeArm'].add([v.index],total*q,'REPLACE')
for i in range(90):
 s.frame_set(i+1);world=rotations[i].copy()
 for side in ('Left','Right'):
  hip,knee,ankle=legs[i][side];hip=hip.copy();hip.z+=float(height[i]-roots[i,2])
  upper=r.data.bones[side+'UpLeg'].length;lower=r.data.bones[side+'Leg'].length
  direction=ankle-hip;distance=direction.length;direction.normalize();d=min(upper+lower-1e-6,max(abs(upper-lower)+1e-6,distance))
  along=(upper*upper-lower*lower+d*d)/(2*d);radius=math.sqrt(max(0,upper*upper-along*along))
  pole=knee-hip;pole-=direction*pole.dot(direction);pole.normalize();new_knee=hip+direction*along+pole*radius
  for part,target in [('UpLeg',new_knee-hip),('Leg',ankle-new_knee)]:
   name=side+part;delta=world[name].col[1].normalized().rotation_difference(target.normalized()).to_matrix();world[name]=delta@world[name]

 for n,p in parents.items():
  local=world[p].inverted()@world[n] if p else world[n];b=r.pose.bones[n];q=(rel[n].to_3x3().inverted()@local).to_quaternion();q.make_compatible(b.rotation_quaternion);b.rotation_quaternion=q;b.keyframe_insert('rotation_quaternion',frame=i+1)
 r.location=roots[i];r.location.z=float(height[i]);r.keyframe_insert('location',frame=i+1)
minimum=[]
for f in range(1,91):
 s.frame_set(f);o=h.evaluated_get(bpy.context.evaluated_depsgraph_get());m=o.to_mesh();minimum.append(min((o.matrix_world@v.co).z for v in m.vertices));o.to_mesh_clear()
lift=-min(minimum)
for i in range(90):
 s.frame_set(i+1);r.location.z=float(height[i]+lift);r.keyframe_insert('location',frame=i+1)
for layer in r.animation_data.action.layers:
 for strip in layer.strips:
  for bag in strip.channelbags:
   for curve in bag.fcurves:
    for key in curve.keyframe_points:key.interpolation='LINEAR'
r['user_elbow_polish']=True;r['preview_loop_frames']=88
s.frame_set(1);bpy.ops.wm.save_as_mainfile(filepath=str(R/'outputs/hero-mixamo-run.blend'),compress=True)
bpy.ops.object.select_all(action='DESELECT');h.select_set(True);r.select_set(True);bpy.context.view_layer.objects.active=r
bpy.ops.export_scene.gltf(filepath=str(R/'outputs/hero-mixamo-run.glb'),use_selection=True,export_animations=True,export_frame_range=True,export_force_sampling=True,export_animation_mode='SCENE')
report={'source':'Unchanged Mixamo FBX; intentional user elbow/root correction','elbow_interior_before_range':[min(before),max(before)],'elbow_interior_after_range':[min(after),max(after)],'root_vertical_second_difference_before':float(np.abs(np.diff(roots[:,2],n=2)).max()),'root_vertical_second_difference_after':float(np.abs(np.diff(height,n=2)).max()),'root_height_range_before':float(np.ptp(roots[:,2])),'root_height_range_after':float(np.ptp(height)),'constant_floor_lift':lift,'floor_min_after':min(minimum)+lift,'ground_clearance_max_after':max(minimum)+lift,'scope':'Fixed-length leg IK preserves prior ankle targets before one constant floor lift; foot sliding and clothing remain separate'}
(R/'docs/logs/hero-mixamo-polish.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report))

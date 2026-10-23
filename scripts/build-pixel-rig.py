"""Fit a fixed-length rig to the current Tripo mesh. Diagnostic poses, NOT running."""
import bpy, math, json, sys
import numpy as np
from pathlib import Path
from mathutils import Vector
from bpy_extras.object_utils import world_to_camera_view
R=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(R/'scripts'))
from pixel_skin import separate_surface,skin_fields,smooth
bpy.ops.wm.open_mainfile(filepath=str(R/'outputs/tripo-pixel-shaped.blend'))
s=bpy.context.scene
hero=next(o for o in s.objects if o.type=='MESH')
mesh=bpy.data.meshes.new_from_object(hero.evaluated_get(bpy.context.evaluated_depsgraph_get()))
hero.shape_key_clear(); hero.data=mesh; hero.name='TripoPixel_Character'
p=np.array([v.co[:] for v in mesh.vertices])
d=np.load(R/'outputs/tripo-pixel-inspection.npz'); colors=d['colors']
assert len(p)==len(colors)
source_positions=p.copy()
mesh,original_ids,regions,face_regions=separate_surface(mesh,colors)
hero.data=mesh;p=np.array([v.co[:] for v in mesh.vertices]);colors=colors[original_ids]
assert np.max(np.abs(p-source_positions[original_ids]))==0
# World-space landmarks measured on this mesh; its anatomy is offset from x=0.
bones={}
def bone(n,h,t,parent=None,deform=True):bones[n]=(h,t,parent,deform)
bone('Root',(.085,0,0),(.085,0,.08),None,False)
bone('Hips',(.085,-.025,.32),(.08,-.02,.39),'Root')
bone('Spine',(.08,-.02,.39),(.075,-.02,.465),'Hips')
bone('Chest',(.075,-.02,.465),(.07,-.02,.565),'Spine')
bone('Neck',(.07,-.02,.565),(.065,-.02,.635),'Chest')
bone('Head',(.065,-.02,.635),(.065,-.02,.91),'Neck')
for side,pts in {
 'L':[(.105,-.03,.53),(.19,-.04,.525),(.295,-.067,.515),(.395,-.09,.505),(.451,-.10,.505)],
 'R':[(.035,-.012,.53),(-.045,.005,.525),(-.145,.015,.515),(-.235,.015,.505),(-.283,.012,.505)]}.items():
 for i,(name,parent) in enumerate([('Clavicle','Chest'),('UpperArm','Clavicle.'+side),('Forearm','UpperArm.'+side),('Hand','Forearm.'+side)]):
  bone(name+'.'+side,pts[i],pts[i+1],parent)
for side,pts in {
 'L':[(.137,-.035,.32),(.173,-.043,.205),(.190,-.040,.095),(.191,-.122,.035),(.193,-.163,.025)],
 'R':[(.032,-.012,.32),(.010,.003,.205),(.002,.012,.095),(-.015,-.065,.035),(-.023,-.102,.025)]}.items():
 for i,(name,parent) in enumerate([('Thigh','Hips'),('Shin','Thigh.'+side),('Foot','Shin.'+side),('Toe','Foot.'+side)]):
  bone(name+'.'+side,pts[i],pts[i+1],parent)
arm=bpy.data.armatures.new('Character proportions - fixed bone lengths')
rig=bpy.data.objects.new('TripoPixel_Rig',arm);s.collection.objects.link(rig)
bpy.ops.object.select_all(action='DESELECT');rig.select_set(True);bpy.context.view_layer.objects.active=rig
bpy.ops.object.mode_set(mode='EDIT')
for n,(h,t,parent,deform) in bones.items():
 b=arm.edit_bones.new(n);b.head=h;b.tail=t;b.use_deform=deform
 if parent:b.parent=arm.edit_bones[parent]
bpy.ops.object.mode_set(mode='OBJECT')
arm.display_type='OCTAHEDRAL';rig.show_in_front=True
for b in arm.bones:b.inherit_scale='NONE'
for b in rig.pose.bones:
 b.rotation_mode='XYZ';b.lock_scale=(True,True,True)
 if b.name!='Root':b.lock_location=(True,True,True)
rig['retarget_policy']='Rotations only below Root. Fixed rest offsets, bone lengths and unit scale. Fit root translation to leg length. No source joint translations.'
rig['source_mesh']='outputs/tripo-pixel-shaped.blend'
rig['motion_status']='Diagnostic joint bends only. No Kimodo motion applied.'
names=[n for n,v in bones.items() if v[3]]
W=skin_fields(p,regions,names)
for j,n in enumerate(names):
 vg=hero.vertex_groups.new(name=n)
 for i in np.flatnonzero(W[:,j]>1e-8):vg.add([int(i)],float(W[i,j]),'REPLACE')
x,y,z=p.T
for region in np.unique(regions):
 vg=hero.vertex_groups.new(name='Region_'+region);vg.add(np.flatnonzero(regions==region).tolist(),1,'REPLACE')
for n,w in [('Cloth_Scarf_Free',(regions=='Scarf')*smooth(.08,.18,.075-x)*(1-smooth(.55,.60,z))),('Cloth_Robe_Free',(regions=='Robe')*smooth(.19,.27,z)*(1-smooth(.38,.48,z))),('Cloth_Hood_Free',(regions=='Hood')*smooth(.65,.75,z)*smooth(.0,.10,y))]:
 vg=hero.vertex_groups.new(name=n)
 for i in np.flatnonzero(w>1e-6):vg.add([int(i)],float(w[i]),'REPLACE')
mod=hero.modifiers.new('Character fixed-length skin','ARMATURE');mod.object=rig;mod.use_deform_preserve_volume=True
hero.parent=rig
s.render.resolution_x=s.render.resolution_y=512;s.cycles.samples=8
s.camera.data.ortho_scale=1.14
center=Vector((.06,0,.49))
projections={}
for angle,label in [(0,'front'),(90,'side')]:
 a=math.radians(angle);s.camera.location=center+Vector((math.sin(a)*3,-math.cos(a)*3,0));s.camera.rotation_euler=(center-s.camera.location).to_track_quat('-Z','Y').to_euler()
 bpy.context.view_layer.update()
 s.render.filepath=str(R/f'outputs/tripo-pixel-rig-{label}.png');bpy.ops.render.render(write_still=True)
 projections[label]={n:[[float(v.x)*512,(1-float(v.y))*512] for pt in [h,t] for v in [world_to_camera_view(s,s.camera,Vector(pt))]] for n,(h,t,_,_) in bones.items() if n!='Root'}
# Neutral geometry must match the evaluated shaped source exactly.
ev=hero.evaluated_get(bpy.context.evaluated_depsgraph_get());q=np.array([v.co[:] for v in ev.data.vertices])
neutral_error=float(np.abs(q-p).max());assert neutral_error<1e-6
# Explicit isolated joint tests: shoulder/arm, knee, torso. These are not a run cycle.
tests=[{}, {'Clavicle.L':(0,0,-8),'Clavicle.R':(0,0,8),'UpperArm.L':(-15,0,-40),'UpperArm.R':(15,0,40),'Forearm.L':(-55,0,0),'Forearm.R':(-55,0,0)}, {'Thigh.L':(35,0,0),'Shin.L':(-65,0,0),'Thigh.R':(-15,0,0),'Shin.R':(-25,0,0)}, {'Chest':(8,0,10),'Neck':(-4,0,-5)} ,{}]
tests += [{'Clavicle.L':(0,0,-8),'Clavicle.R':(0,0,8),'UpperArm.L':(-15,0,-70),'UpperArm.R':(15,0,70),'Forearm.L':(-55,0,0),'Forearm.R':(-55,0,0)},{}]
s.frame_start=1;s.frame_end=121;s.render.fps=30
for f,pose in zip([1,21,41,61,81,101,121],tests):
 for pb in rig.pose.bones:
  pb.rotation_euler=tuple(math.radians(v) for v in pose.get(pb.name,(0,0,0)));pb.keyframe_insert('rotation_euler',frame=f,group=pb.name)
 if pose:s.timeline_markers.new(['Neutral','Shoulder and elbow test','Knee test','Torso test','Neutral','Arms lowered 70 degrees','Neutral'][[1,21,41,61,81,101,121].index(f)],frame=f)
base_lengths={b.name:b.length for b in arm.bones};max_length_error=0;max_scale_error=0;max_local_translation=0
edges=np.array([e.vertices[:] for e in hero.data.edges]);base=np.linalg.norm(p[edges[:,0]]-p[edges[:,1]],axis=1);valid=base>1e-4
pose_reports=[]
for f in range(1,s.frame_end+1):
 s.frame_set(f);bpy.context.view_layer.update()
 for pb in rig.pose.bones:
  max_length_error=max(max_length_error,abs((pb.tail-pb.head).length-base_lengths[pb.name]))
  max_scale_error=max(max_scale_error,max(abs(v-1) for v in pb.scale))
  max_local_translation=max(max_local_translation,pb.location.length)
 if f in [21,41,61,101]:
  ev=hero.evaluated_get(bpy.context.evaluated_depsgraph_get());q=np.array([v.co[:] for v in ev.data.vertices])
  ratios=np.linalg.norm(q[edges[:,0]]-q[edges[:,1]],axis=1)[valid]/base[valid]
  pose_reports.append({'frame':f,'edge_stretch_p99':float(np.quantile(ratios,.99)),'edge_stretch_max':float(ratios.max()),'edges_over_2x':int((ratios>2).sum())})
  s.camera.location=center+Vector((1.8,-3,0));s.camera.rotation_euler=(center-s.camera.location).to_track_quat('-Z','Y').to_euler()
  s.render.filepath=str(R/f'outputs/tripo-pixel-rig-test-{f}.png');bpy.ops.render.render(write_still=True)
assert max_length_error<1e-6 and max_scale_error==0 and max_local_translation==0
s.frame_set(1);s.camera.location=center+Vector((0,-3,0));s.camera.rotation_euler=(center-s.camera.location).to_track_quat('-Z','Y').to_euler()
bpy.ops.wm.save_as_mainfile(filepath=str(R/'outputs/tripo-pixel-rig.blend'),compress=True)
report={'source':'outputs/tripo-pixel-shaped.blend','bones':len(bones),'vertices':len(p),'original_vertices':len(source_positions),'surface_geometry_error_m':float(np.abs(p-source_positions[original_ids]).max()),'region_face_counts':{r:face_regions.count(r) for r in set(face_regions)},'neutral_max_error_m':neutral_error,'bone_length_max_error_m':max_length_error,'scale_max_error':max_scale_error,'local_translation_max_m':max_local_translation,'weight_sum_max_error':float(np.abs(W.sum(1)-1).max()),'test_frames':s.frame_end,'poses':pose_reports,'cloth_simulated':False,'kimodo_applied':False,'landmarks':bones,'projections':projections}
(R/'docs/logs/pixel-rig.json').write_text(json.dumps(report,indent=2))
print(json.dumps({k:v for k,v in report.items() if k not in ['landmarks','projections']}),flush=True)

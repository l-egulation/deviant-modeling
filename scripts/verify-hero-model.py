"""Validate bind separation, new quad topology, skinning and shoulder response."""
import bpy,bmesh,json,math
import numpy as np
from pathlib import Path
from mathutils import Vector,Quaternion
ROOT=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(ROOT/'outputs/hero-model.blend'))
s=bpy.context.scene;r=bpy.data.objects['HeroModelRig'];coat=bpy.data.objects['Hero_Coat']
assert len(r.data.bones)==18
for side,sign in (('Left',1),('Right',-1)):
    a=r.data.bones[side+'Arm'];f=r.data.bones[side+'ForeArm'];leg=r.data.bones[side+'Leg']
    assert abs(a.head_local.z-a.tail_local.z)<1e-6 and abs(f.head_local.z-f.tail_local.z)<1e-6
    assert sign*f.tail_local.x>.37 and sign*leg.tail_local.x>.18
    assert a.parent.name==side+'Clavicle'
bm=bmesh.new();bm.from_mesh(coat.data)
nonmanifold=sum(len(e.link_faces)>2 for e in bm.edges);boundary=sum(e.is_boundary for e in bm.edges)
assert nonmanifold==0 and boundary==104,(nonmanifold,boundary)
vertices=set(bm.verts);components=0
while vertices:
    components+=1;stack=[vertices.pop()]
    while stack:
        for edge in stack.pop().link_edges:
            for v in edge.verts:
                if v in vertices:vertices.remove(v);stack.append(v)
bm.free();assert components==1
assert all(len(p.vertices)==4 for p in coat.data.polygons)
parts=[o for o in s.objects if o.type=='MESH'];weight_error=0
for obj in parts:
    weight_error=max(weight_error,max(abs(sum(g.weight for g in v.groups)-1) for v in obj.data.vertices))
assert weight_error<1e-5
rest=np.array([v.co[:] for v in coat.data.vertices]);edges=np.array([e.vertices[:] for e in coat.data.edges]);length=np.linalg.norm(rest[edges[:,0]]-rest[edges[:,1]],axis=1)
valid=length>.002;peak=0;p99=0;min_scale=1;max_scale=1;worst=None
pants=[];pants_peak=0;pants_p99=0
for name in ('Hero_LeftTrouser','Hero_RightTrouser'):
    obj=bpy.data.objects[name];v=np.array([v.co[:] for v in obj.data.vertices]);e=np.array([e.vertices[:] for e in obj.data.edges]);l=np.linalg.norm(v[e[:,0]]-v[e[:,1]],axis=1)
    pants.append((obj,e,l))
# Cage geometry is the deformation surface before subdivision and thickness.
for obj in [coat]+[p[0] for p in pants]:
    for m in obj.modifiers:
        if m.type in ('SUBSURF','SOLIDIFY'):m.show_viewport=False
for frame in range(1,121):
    s.frame_set(frame)
    obj=coat.evaluated_get(s.view_layers[0].depsgraph);mesh=obj.to_mesh();co=np.array([v.co[:] for v in mesh.vertices]);obj.to_mesh_clear()
    assert np.isfinite(co).all() and len(co)==len(rest)
    ratio=np.linalg.norm(co[edges[valid,0]]-co[edges[valid,1]],axis=1)/length[valid]
    if float(ratio.max())>peak:
        edge=edges[np.flatnonzero(valid)[int(np.argmax(ratio))]];worst={'frame':frame,'rest_edge_positions':rest[edge].tolist()}
    peak=max(peak,float(ratio.max()));p99=max(p99,float(np.percentile(ratio,99)))
    for b in r.pose.bones:
        min_scale=min(min_scale,*b.scale);max_scale=max(max_scale,*b.scale)
    for obj,e,l in pants:
        evaluated=obj.evaluated_get(s.view_layers[0].depsgraph);mesh=evaluated.to_mesh();v=np.array([v.co[:] for v in mesh.vertices]);evaluated.to_mesh_clear();ratio=np.linalg.norm(v[e[:,0]]-v[e[:,1]],axis=1)/l
        pants_peak=max(pants_peak,float(ratio.max()));pants_p99=max(pants_p99,float(np.percentile(ratio,99)))
assert max_scale-min_scale<1e-6
# Isolate the actual shoulder surface, rather than checking only bone origins.
r.animation_data_clear();r.location=(0,0,0)
for b in r.pose.bones:b.rotation_quaternion=(1,0,0,0)
s.view_layers[0].update()
mask=(rest[:,0]>.075)&(rest[:,0]<.18)&(rest[:,2]>.47)&(rest[:,2]<.555)
displacements=[]
for deg in (-15,15):
    b=r.pose.bones['LeftClavicle'];axis=b.bone.matrix_local.to_3x3().inverted() @ Vector((0,0,1));b.rotation_quaternion=Quaternion(axis,math.radians(deg));s.view_layers[0].update()
    obj=coat.evaluated_get(s.view_layers[0].depsgraph);mesh=obj.to_mesh();displacements.append(np.array([v.co[:] for v in mesh.vertices])[mask]);obj.to_mesh_clear()
response=np.linalg.norm(displacements[1]-displacements[0],axis=1)
median=float(np.median(response));assert median>.005,median
for b in r.pose.bones:b.rotation_quaternion=(1,0,0,0)
hip_peak=0
for deg in (-25,25):
    for side in ('Left','Right'):
        bone=r.pose.bones[side+'UpLeg'];axis=bone.bone.matrix_local.to_3x3().inverted() @ Vector((1,0,0));bone.rotation_quaternion=Quaternion(axis,math.radians(deg))
    s.view_layers[0].update()
    for obj,e,l in pants:
        evaluated=obj.evaluated_get(s.view_layers[0].depsgraph);mesh=evaluated.to_mesh();v=np.array([v.co[:] for v in mesh.vertices]);evaluated.to_mesh_clear()
        hip_peak=max(hip_peak,float((np.linalg.norm(v[e[:,0]]-v[e[:,1]],axis=1)/l).max()))
report={'status':'PASS' if peak<2 and p99<1.6 else 'FAIL','rig_bones':18,'coat_connected_components':components,'coat_quads':len(coat.data.polygons),'coat_nonmanifold_branch_edges':nonmanifold,'intentional_open_boundary_edges':boundary,'normalized_weight_error':weight_error,'joint_test_frames':120,'max_coat_edge_stretch':peak,'worst_frame_p99_coat_edge_stretch':p99,'isolated_clavicle_30deg_surface_median_displacement_m':median,'pose_bone_scales':[min_scale,max_scale],'scope':'New deform cage and isolated shoulder coupling. Not final cloth collision or animation art approval.'}
report['worst']=worst
report.update(max_trouser_edge_stretch=pants_peak,worst_frame_p99_trouser_edge_stretch=pants_p99)
report.update(hip_swing_test_degrees=25,max_hip_swing_trouser_edge_stretch=hip_peak)
if pants_peak>=2 or pants_p99>=1.8:report['status']='FAIL'
if hip_peak>=2:report['status']='FAIL'
(ROOT/'docs/logs/hero-model-check.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
assert peak<2 and p99<1.6,'New coat still stretches excessively in joint test'
assert pants_peak<2 and pants_p99<1.8,'Trouser knee deformation needs correction'
assert hip_peak<2,'Hip attachment deformation needs correction'

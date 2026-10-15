"""Check normalized skin weights, fitted dimensions, floor and GLB poses."""
import bpy,json,os,numpy as np
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
STEM=os.environ.get('RUN_STEM','tripo-run')
bpy.ops.wm.open_mainfile(filepath=str(ROOT/f'outputs/{STEM}.blend'))
scene=bpy.context.scene;rig=bpy.data.objects['TripoRunRig'];hero=bpy.data.objects['TripoHero']
weights=[sum(g.weight for g in v.groups) for v in hero.data.vertices]
error=max(abs(w-1) for w in weights);assert error<1e-5
poses={};bottom=[];scale_error=0
contact_points={};roots=[];cycle_error=0;ankle_angles=[]
for f in range(1,91):
    scene.frame_set(f)
    scale_error=max(scale_error,max(abs(s-1) for b in rig.pose.bones for s in b.scale))
    import math
    ankle_angles.extend(math.degrees(2*math.acos(min(1,abs(rig.pose.bones[s+'Foot'].rotation_quaternion.normalized().w)))) for s in ('Left','Right'))
    obj=hero.evaluated_get(bpy.context.evaluated_depsgraph_get());mesh=obj.to_mesh()
    points=np.array([(obj.matrix_world@v.co)[:] for v in mesh.vertices]);obj.to_mesh_clear()
    bottom.append(float(points[:,2].min()))
    if 'run_cycle_seconds' in rig:
        roots.append(rig.location.copy())
        i=f-1
        if i%9<6:
            side='Left' if (i//9)%2==0 else 'Right';sign=1 if side=='Left' else -1
            base=np.array([v.co[:] for v in hero.data.vertices])
            sole=base[(base[:,0]*sign>0)&(base[:,2]<.075)]-np.array(rig.data.bones[side+'Foot'].head_local)
            lowest=sole[sole[:,2]<sole[:,2].min()+.002];pivot=lowest[np.argmin(lowest[:,1])]
            foot=rig.pose.bones[side+'Foot']
            rotation=foot.matrix.to_3x3().normalized()@foot.bone.matrix_local.to_3x3().inverted()
            from mathutils import Vector
            p=rig.matrix_world@foot.head+rotation@Vector(pivot)
            contact_points.setdefault(i//9,[]).append(p[:])
    if f in (1,30,60,90):poses[f]=np.stack([points.min(0),points.max(0)])
assert scale_error<1e-6
assert min(bottom)>-.001, min(bottom)
authored={}
if roots:
    drift=max(float(np.ptp(np.array(p),axis=0).max()) for p in contact_points.values())
    scene.frame_set(1);first={b.name:b.rotation_quaternion.copy() for b in rig.pose.bones}
    scene.frame_set(19)
    cycle_error=max(1-abs(q.dot(rig.pose.bones[n].rotation_quaternion)) for n,q in first.items())
    acceleration=float(np.abs(np.diff(np.array(roots)[:,2],n=2)).max())
    authored={'stance_toe_world_drift_m':drift,'cycle_quaternion_error':cycle_error,'root_vertical_second_difference_max_m':acceleration}
    assert drift<.005, authored
    assert cycle_error<1e-5, authored
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.context.scene.render.fps=30
bpy.ops.import_scene.gltf(filepath=str(ROOT/f'outputs/{STEM}.glb'))
rig=next(o for o in bpy.context.scene.objects if o.type=='ARMATURE')
meshes=[o for o in bpy.context.scene.objects if o.type=='MESH' and o.parent==rig]
assert len(rig.data.bones)==18 and meshes
errors=[]
for f,wanted in poses.items():
    bpy.context.scene.frame_set(f)
    points=[]
    for obj in meshes:
        evaluated=obj.evaluated_get(bpy.context.evaluated_depsgraph_get());mesh=evaluated.to_mesh()
        points.extend([(evaluated.matrix_world@v.co)[:] for v in mesh.vertices]);evaluated.to_mesh_clear()
    points=np.array(points);bounds=np.stack([points.min(0),points.max(0)])
    errors.append(float(np.abs(bounds-wanted).max()))
assert max(errors)<.001, errors
report={'weight_sum_max_error':error,'bone_scale_error':scale_error,'floor_min_m':min(bottom),
        'glb_pose_bound_max_error_m':max(errors),'frames_checked':90,'bones':18,
        'scope':'Structural validation PASS; does not certify visual clothing quality'}
report.update(authored)
report['ankle_rotation_from_bind_max_degrees']=max(ankle_angles)
(ROOT/f'docs/logs/{STEM}-validation.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report))

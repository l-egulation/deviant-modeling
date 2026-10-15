"""Check normalized skin weights, fitted dimensions, floor and GLB poses."""
import bpy,json,numpy as np
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(ROOT/'outputs/tripo-run.blend'))
scene=bpy.context.scene;rig=bpy.data.objects['TripoRunRig'];hero=bpy.data.objects['TripoHero']
weights=[sum(g.weight for g in v.groups) for v in hero.data.vertices]
error=max(abs(w-1) for w in weights);assert error<1e-5
poses={};bottom=[];scale_error=0
for f in range(1,91):
    scene.frame_set(f)
    scale_error=max(scale_error,max(abs(s-1) for b in rig.pose.bones for s in b.scale))
    obj=hero.evaluated_get(bpy.context.evaluated_depsgraph_get());mesh=obj.to_mesh()
    points=np.array([(obj.matrix_world@v.co)[:] for v in mesh.vertices]);obj.to_mesh_clear()
    bottom.append(float(points[:,2].min()))
    if f in (1,30,60,90):poses[f]=np.stack([points.min(0),points.max(0)])
assert scale_error<1e-6
assert min(bottom)>-.001, min(bottom)
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.context.scene.render.fps=30
bpy.ops.import_scene.gltf(filepath=str(ROOT/'outputs/tripo-run.glb'))
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
(ROOT/'docs/logs/tripo-run-validation.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report))

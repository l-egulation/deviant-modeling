"""Measure deformation and render the new Tripo/Kimodo run for visual review."""
import bpy
import json
import os
import numpy as np
from pathlib import Path
from mathutils import Vector
ROOT=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(ROOT/'outputs/tripo-run.blend'))
scene=bpy.context.scene;hero=bpy.data.objects['TripoHero'];rig=bpy.data.objects['TripoRunRig']
vertices=np.array([v.co[:] for v in hero.data.vertices])
edges=np.array([e.vertices[:] for e in hero.data.edges])
length=np.linalg.norm(vertices[edges[:,0]]-vertices[edges[:,1]],axis=1)
valid=length>.002
valid_ids=np.flatnonzero(valid)
dest=ROOT/'.cache/tripo-run-frames';dest.mkdir(parents=True,exist_ok=True)
samples=[];stretch=[];bottom=[]
frames=range(1,91) if os.environ.get('FULL_RENDER')=='1' else [1,8,16,24,32,40]
for f in frames:
    scene.frame_set(f)
    evaluated=hero.evaluated_get(bpy.context.evaluated_depsgraph_get());mesh=evaluated.to_mesh()
    points=np.array([(evaluated.matrix_world@v.co)[:] for v in mesh.vertices])
    ratio=np.linalg.norm(points[edges[:,0]]-points[edges[:,1]],axis=1)[valid]/length[valid]
    stretch.append(float(ratio.max()));bottom.append(float(points[:,2].min()))
    samples.append({'frame':f,'edge_stretch_max':float(ratio.max()),'edge_stretch_p99':float(np.quantile(ratio,.99)),'bottom':float(points[:,2].min())})
    if f==8:
        details=[]
        for e in valid_ids[np.argsort(ratio)[-12:]]:
            details.append({'rest':vertices[edges[e]].tolist(),'ratio':float(np.linalg.norm(points[edges[e,0]]-points[edges[e,1]])/length[e]),
                'weights':[{hero.vertex_groups[g.group].name:g.weight for g in hero.data.vertices[int(i)].groups} for i in edges[e]]})
        (ROOT/'docs/logs/tripo-run-edge-audit.json').write_text(json.dumps(details,indent=2))
    evaluated.to_mesh_clear()
    scene.render.filepath=str(dest/f'{f:03d}.png');bpy.ops.render.render(write_still=True)
report={'scope':'Measured deformation; visual art review is separate','frames':samples,'maximum_edge_stretch':max(stretch),'lowest_point':min(bottom)}
(ROOT/'docs/logs/tripo-run-deformation.json').write_text(json.dumps(report,indent=2)+'\n')
for label,offset in [('side',Vector((2.7,0,.10))),('front',Vector((0,-2.7,.10)))]:
    for f in [1,8,16,24,32,40]:
        scene.frame_set(f);center=Vector((rig.location.x,rig.location.y,.49))
        scene.camera.animation_data_clear();scene.camera.location=center+offset
        scene.camera.rotation_euler=(-offset).to_track_quat('-Z','Y').to_euler()
        scene.render.filepath=str(ROOT/f'.cache/tripo-run-{label}-{f:03d}.png');bpy.ops.render.render(write_still=True)

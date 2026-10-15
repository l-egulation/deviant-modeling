"""Reject local sleeve stretching that whole-body bounds checks miss."""
import bpy,json,os
import numpy as np
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
path=Path(os.environ.get('HERO_ARM_BLEND',str(ROOT/'outputs/hero-run.blend')))
bpy.ops.wm.open_mainfile(filepath=str(path))
hero=bpy.data.objects['InkHero'];scene=bpy.context.scene
rest=np.array([v.co[:] for v in hero.data.vertices])
edges=np.array([e.vertices[:] for e in hero.data.edges])
length=np.linalg.norm(rest[edges[:,0]]-rest[edges[:,1]],axis=1)
arm=(np.abs(rest[:,0])>.13)&(rest[:,2]>.33)&(rest[:,2]<.565)
ids=np.flatnonzero(arm[edges].all(1)&(length>.002))
points,inverse=np.unique(np.round(rest,5),axis=0,return_inverse=True)
counts=np.bincount(inverse)
seams=(counts>1)&(np.abs(points[:,0])>.13)&(points[:,2]>.33)&(points[:,2]<.565)
peak=0;worst=None;ratios=[];seam_gap=0
for f in range(1,91):
    scene.frame_set(f)
    obj=hero.evaluated_get(bpy.context.evaluated_depsgraph_get());mesh=obj.to_mesh()
    coords=np.empty(len(mesh.vertices)*3);mesh.vertices.foreach_get('co',coords);coords=coords.reshape(-1,3)
    low=np.full((len(points),3),np.inf);high=np.full_like(low,-np.inf)
    np.minimum.at(low,inverse,coords);np.maximum.at(high,inverse,coords)
    seam_gap=max(seam_gap,float(np.linalg.norm((high-low)[seams],axis=1).max()))
    ratio=np.linalg.norm(coords[edges[ids,0]]-coords[edges[ids,1]],axis=1)/length[ids]
    i=int(np.argmax(ratio));value=float(ratio[i]);ratios.extend(ratio.tolist())
    if value>peak:peak=value;worst={'frame':f,'vertices':edges[ids[i]].tolist(),'rest_edge_m':float(length[ids[i]])}
    obj.to_mesh_clear()
report={'status':'PASS' if peak<5 and seam_gap<.0001 else 'FAIL','frames':90,'arm_edges_per_frame':len(ids),'max_arm_edge_stretch':peak,'p99_arm_edge_stretch':float(np.percentile(ratios,99)),'max_coincident_arm_seam_gap_m':seam_gap,'worst':worst,'threshold':5,'scope':'Local sleeve deformation; excludes tiny edges below 2mm. Not a cloth-collision or artistic-quality certificate.'}
print(json.dumps(report,indent=2))
if 'HERO_ARM_BLEND' not in os.environ:(ROOT/'docs/logs/hero-run-arm-check.json').write_text(json.dumps(report,indent=2)+'\n')
assert peak<5,f'Arm edge stretched {peak:.2f} times its rest length'
assert seam_gap<.0001,f'UV-split arm surface opened by {seam_gap:.6f}m'

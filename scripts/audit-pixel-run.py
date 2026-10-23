import bpy,numpy as np,json
from pathlib import Path
R=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(R/'outputs/pixel-run.blend'))
s=bpy.context.scene;h=bpy.data.objects['TripoPixel_Character'];rig=bpy.data.objects['TripoPixel_Rig'];p=np.array([v.co[:] for v in h.data.vertices]);edges=np.array([e.vertices[:] for e in h.data.edges]);length=np.linalg.norm(p[edges[:,0]]-p[edges[:,1]],axis=1);valid=length>1e-4
worst=[]
for f in range(1,91):
 s.frame_set(f);bpy.context.view_layer.update();q=np.array([v.co[:] for v in h.evaluated_get(bpy.context.evaluated_depsgraph_get()).data.vertices]);ratio=np.linalg.norm(q[edges[:,0]]-q[edges[:,1]],axis=1)/np.maximum(length,1e-9);ratio[~valid]=0
 k=int(ratio.argmax());worst.append({'frame':f,'max_edge':float(ratio[k]),'rest_points':p[edges[k]].tolist()})
worst.sort(key=lambda v:-v['max_edge']);(R/'docs/logs/pixel-run-audit.json').write_text(json.dumps(worst,indent=2));print(json.dumps(worst[:5]),flush=True)

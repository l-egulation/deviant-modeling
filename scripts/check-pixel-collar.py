"""Measure coincident collar boundary separation throughout the saved run."""
import bpy, numpy as np, json, os
from pathlib import Path
R=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(R/os.environ.get('COLLAR_INPUT','outputs/pixel-run.blend')))
h=bpy.data.objects['TripoPixel_Character'];s=bpy.context.scene
p=np.array([v.co[:] for v in h.data.vertices])
labels=[next(h.vertex_groups[g.group].name[7:] for g in v.groups if h.vertex_groups[g.group].name.startswith('Region_')) for v in h.data.vertices]
bins={}
for i,co in enumerate(p):bins.setdefault(tuple(np.round(co,6)),[]).append(i)
pairs=[]
for ids in bins.values():
 for a in ids:
  for b in ids:
   if labels[a]=='Scarf' and labels[b] in ['Robe','Arm.L','Arm.R'] and p[a,2]>.48 and p[a,0]>-.005:pairs.append((a,b))
assert pairs
pairs=np.array(pairs);errors=[]
for f in range(1,91):
 s.frame_set(f);bpy.context.view_layer.update()
 q=np.array([v.co[:] for v in h.evaluated_get(bpy.context.evaluated_depsgraph_get()).data.vertices])
 errors.append(float(np.linalg.norm(q[pairs[:,0]]-q[pairs[:,1]],axis=1).max()))
report={'pairs':len(pairs),'max_gap_m':max(errors),'per_frame_gap_m':errors,'materials':[{ 'name':m.name,'alpha':[(n.inputs['Alpha'].default_value,bool(n.inputs['Alpha'].is_linked)) for n in m.node_tree.nodes if n.type=='BSDF_PRINCIPLED']} for m in h.data.materials]}
tag=os.environ.get('COLLAR_TAG','before')
(R/f'docs/logs/pixel-collar-{tag}.json').write_text(json.dumps(report,indent=2))
print(json.dumps(report))
if tag in ['after','cloth']:assert max(errors)<1e-5

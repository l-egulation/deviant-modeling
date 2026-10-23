"""Check actual baked triangles; coarse cage collisions are not sufficient evidence."""
import bpy,numpy as np,json,os
from pathlib import Path
from mathutils.bvhtree import BVHTree
R=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(R/os.environ.get('VERIFY_INPUT','outputs/pixel-run-cloth.blend')))
h=bpy.data.objects['TripoPixel_Character'];keys=h.data.shape_keys.key_blocks
p=np.array([v.co[:] for v in keys[0].data])
labels=np.array([next(h.vertex_groups[g.group].name[7:] for g in v.groups if h.vertex_groups[g.group].name.startswith('Region_')) for v in h.data.vertices])
robe=[];scarf=[]
for poly in h.data.polygons:
 ids=list(poly.vertices);q=p[ids];c=q.mean(0);n=np.cross(q[1]-q[0],q[2]-q[0])
 if np.all(labels[ids]=='Robe') and .19<c[2]<.50 and np.dot(n[:2],c[:2]-[.085,-.025])>0:robe.append(ids)
 if np.all(labels[ids]=='Scarf') and c[0]<-.05 and c[1]>.015:scarf.append(ids)
def crosses(tri,other):
 a,b,c=other;e1=b-a;e2=c-a
 for i in range(3):
  start=tri[i];direction=tri[(i+1)%3]-start;v=np.cross(direction,e2);det=np.dot(e1,v)
  if abs(det)<1e-12:continue
  ss=start-a;u=np.dot(ss,v)/det
  if not 0<u<1:continue
  q=np.cross(ss,e1);w=np.dot(direction,q)/det;t=np.dot(e2,q)/det
  if 0<w and u+w<1 and 1e-6<t<1-1e-6:return True
 return False
render_edges=set()
for poly in h.data.polygons:
 ids=list(poly.vertices)
 for i in range(len(ids)):render_edges.add(tuple(sorted((ids[i],ids[(i+1)%len(ids)]))))
edges=np.array(sorted(render_edges));length=np.linalg.norm(p[edges[:,0]]-p[edges[:,1]],axis=1);valid=length>1e-4
rows=[]
for f in range(1,91):
 q=np.array([v.co[:] for v in keys[f'Run cloth {f:03d}'].data]);assert np.isfinite(q).all()
 a=BVHTree.FromPolygons(q.tolist(),robe,all_triangles=True);b=BVHTree.FromPolygons(q.tolist(),scarf,all_triangles=True)
 hits=sum(crosses(q[robe[i]],q[scarf[j]]) or crosses(q[scarf[j]],q[robe[i]]) for i,j in a.overlap(b))
 ratio=np.linalg.norm(q[edges[:,0]]-q[edges[:,1]],axis=1)/np.maximum(length,1e-9)
 ratio[~valid]=0;k=int(ratio.argmax())
 rows.append({'frame':f,'scarf_robe_intersections':int(hits),'max_edge_stretch':float(ratio[k]),'worst_rest_edge':p[edges[k]].tolist(),'worst_regions':labels[edges[k]].tolist(),'min_z':float(q[:,2].min())})
report={'scope':'90 frames; noncoplanar rendered outer robe/scarf-tail intersections; excludes attachments, self-collision and continuous collision','robe_triangles':len(robe),'scarf_triangles':len(scarf),'frames_with_intersections':sum(r['scarf_robe_intersections']>0 for r in rows),'max_pairs':max(r['scarf_robe_intersections'] for r in rows),'max_edge_stretch':max(r['max_edge_stretch'] for r in rows),'frames':rows}
(R/os.environ.get('VERIFY_OUTPUT','docs/logs/pixel-run-cloth-validation.json')).write_text(json.dumps(report,indent=2));print(json.dumps({k:v for k,v in report.items() if k!='frames'}))

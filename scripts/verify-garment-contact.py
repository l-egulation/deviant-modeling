"""Check baked render triangles, not just the coarse simulation surfaces."""
import bpy,json,numpy as np,os
from pathlib import Path
from mathutils.bvhtree import BVHTree
R=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(R/os.environ.get('CONTACT_INPUT','outputs/tripo-pixel-cloth-test.blend')))
ob=bpy.data.objects['TripoPixel_Working'];keys=ob.data.shape_keys.key_blocks
rest=np.array([v.co[:] for v in keys[0].data]);colors=np.load(R/'outputs/tripo-pixel-inspection.npz')['colors']
teal=(colors[:,2]-colors[:,0]>.08)&(colors[:,1]>.15)
robe=[];scarf=[]
for poly in ob.data.polygons:
    ids=list(poly.vertices);q=rest[ids];c=q.mean(0);n=np.cross(q[1]-q[0],q[2]-q[0])
    if .215<c[2]<.54 and teal[ids].mean()<.25 and np.dot(n[:2],c[:2])>0 and .065<np.linalg.norm(c[:2])<.22:robe.append(ids)
    if c[0]<-.03 and c[1]>0 and .20<c[2]<.56 and teal[ids].mean()>.7:scarf.append(ids)
face=(rest[:,1]<-.08)&(rest[:,2]>.66)&(colors[:,0]<.5)
def cross_edge(tri,other):
    # Segment / triangle intersections; exclude endpoints and coplanar contacts.
    a,b,c=other;e1=b-a;e2=c-a
    for i in range(3):
        start=tri[i];direction=tri[(i+1)%3]-start
        h=np.cross(direction,e2);det=np.dot(e1,h)
        if abs(det)<1e-12:continue
        s=start-a;u=np.dot(s,h)/det
        if not 0<u<1:continue
        q=np.cross(s,e1);v=np.dot(direction,q)/det;t=np.dot(e2,q)/det
        if 0<v and u+v<1 and 1e-6<t<1-1e-6:return True
    return False
rows=[]
for f in range(1,151):
    p=np.array([v.co[:] for v in keys[f'Physical bake {f:03d}'].data])
    a=BVHTree.FromPolygons(p.tolist(),robe,all_triangles=True)
    b=BVHTree.FromPolygons(p.tolist(),scarf,all_triangles=True)
    candidates=a.overlap(b);hits=0
    for i,j in candidates:
        r=p[robe[i]];s=p[scarf[j]]
        hits+=bool(cross_edge(r,s) or cross_edge(s,r))
    rows.append({'frame':f,'candidate_pairs':len(candidates),'intersecting_triangle_pairs':hits,'face_displacement_max':float(np.linalg.norm((p-rest)[face],axis=1).max())})
report={'scope':'150 baked frames; rendered outer robe and scarf tail excluding neck attachment; noncoplanar edge/triangle intersections','robe_triangles':len(robe),'scarf_triangles':len(scarf),'frames_with_intersection':sum(r['intersecting_triangle_pairs']>0 for r in rows),'max_intersecting_pairs':max(r['intersecting_triangle_pairs'] for r in rows),'face_displacement_max':max(r['face_displacement_max'] for r in rows),'frames':rows}
(R/os.environ.get('CONTACT_REPORT','docs/logs/garment-contact.json')).write_text(json.dumps(report,indent=2))
print(json.dumps({k:v for k,v in report.items() if k!='frames'}))

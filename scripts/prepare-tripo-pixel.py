"""Create a reduced working copy; preserve the downloaded Tripo source."""
import bpy, bmesh, json
import math
from mathutils import Vector
from pathlib import Path
from collections import Counter

ROOT=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(ROOT/'outputs/tripo-pixel.blend'))
obj=next(o for o in bpy.context.scene.objects if o.type=='MESH')
obj.name='TripoPixel_Working'
bpy.context.view_layer.objects.active=obj
obj.select_set(True)
original=len(obj.data.polygons)
mod=obj.modifiers.new('Working mesh reduction','DECIMATE')
mod.ratio=60000/original
bpy.ops.object.modifier_apply(modifier=mod.name)
bm=bmesh.new(); bm.from_mesh(obj.data)
# UV seams can duplicate vertices; weld only coincident positions for diagnosis.
bmesh.ops.remove_doubles(bm,verts=list(bm.verts),dist=0.000001)
seen=set(); components=[]
for v in bm.verts:
    if v in seen: continue
    stack=[v]; seen.add(v); points=[]
    while stack:
        p=stack.pop(); points.append(tuple(p.co))
        for e in p.link_edges:
            q=e.other_vert(p)
            if q not in seen: seen.add(q); stack.append(q)
    components.append({'vertices':len(points),'min':[min(p[i] for p in points) for i in range(3)],'max':[max(p[i] for p in points) for i in range(3)]})
report={'source':'assets/hero-pixel-tripo.glb','original_faces':original,'working_faces':len(obj.data.polygons),'working_vertices':len(obj.data.vertices),'connected_components_after_coincident_weld':sorted(components,key=lambda x:-x['vertices']),'boundary_edges_after_weld':sum(e.is_boundary for e in bm.edges),'nonmanifold_edges_after_weld':sum(not e.is_manifold for e in bm.edges),'cloth_ready':False,'note':'Reduction is a working copy only. No cloth, rig, or motion; component diagnosis does not imply anatomical separation.'}
bm.free()
out=ROOT/'outputs/tripo-pixel-working.blend'
bpy.ops.wm.save_as_mainfile(filepath=str(out),compress=True)
(ROOT/'docs/logs/tripo-pixel-topology.json').write_text(json.dumps(report,indent=2))
print(json.dumps(report))
camera=bpy.context.scene.camera
center=Vector((0,0,0.489395))
for angle,label in [(0,'front'),(90,'side')]:
    a=math.radians(angle)
    camera.location=center+Vector((math.sin(a)*3,-math.cos(a)*3,0))
    camera.rotation_euler=(center-camera.location).to_track_quat('-Z','Y').to_euler()
    bpy.context.scene.render.filepath=str(ROOT/f'outputs/tripo-pixel-working-{label}.png')
    bpy.ops.render.render(write_still=True)

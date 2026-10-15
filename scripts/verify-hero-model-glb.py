"""Round-trip the rebuilt multi-part skinned model at three test poses."""
import bpy,json
import numpy as np
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def bounds():
    points=[]
    for obj in bpy.context.scene.objects:
        # Blender's importer may add an unparented Icosphere for bone display.
        # Only the exported, skinned model parts belong in the geometry bounds.
        if obj.type!='MESH' or obj.parent is None or obj.parent.type!='ARMATURE':continue
        evaluated=obj.evaluated_get(bpy.context.evaluated_depsgraph_get());mesh=evaluated.to_mesh()
        points.extend((evaluated.matrix_world @ v.co)[:] for v in mesh.vertices);evaluated.to_mesh_clear()
    p=np.array(points);assert np.isfinite(p).all();return np.stack((p.min(0),p.max(0)))
bpy.ops.wm.open_mainfile(filepath=str(ROOT/'outputs/hero-model.blend'));s=bpy.context.scene
expected=[]
for frame in (1,60,120):s.frame_set(frame);expected.append(bounds())
for obj in list(bpy.data.objects):bpy.data.objects.remove(obj,do_unlink=True)
for a in list(bpy.data.actions):bpy.data.actions.remove(a)
bpy.ops.import_scene.gltf(filepath=str(ROOT/'outputs/hero-model.glb'))
r=next(o for o in s.objects if o.type=='ARMATURE');assert len(r.data.bones)==18
start,end=r.animation_data.action.frame_range;actual=[]
for frame in (start,start+59,end):s.frame_set(int(round(frame)));actual.append(bounds())
errors=[float(np.abs(a-b).max()) for a,b in zip(actual,expected)]
print(json.dumps({'expected_bounds':[p.tolist() for p in expected],'imported_bounds':[p.tolist() for p in actual],'action_range':[float(start),float(end)]},indent=2))
assert max(errors)<.001,errors
assert np.abs(actual[0]-actual[1]).max()>.03
report={'status':'PASS','bones':18,'skinned_mesh_parts':sum(o.type=='MESH' and o.parent==r for o in s.objects),'max_animated_bounds_difference_m':max(errors),'sample_errors_m':errors,'imported_frame_range':[float(start),float(end)],'scope':'Re-imported rebuilt rig and joint-test animation; pose bounds, not final running motion. Importer bone-display helper excluded.'}
(ROOT/'docs/logs/hero-model-glb-check.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))

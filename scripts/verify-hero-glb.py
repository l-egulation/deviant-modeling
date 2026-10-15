"""Re-import exported GLB and compare animated bounds with the Blender scene."""
import os
import bpy
import json
import numpy as np
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MOTION = os.environ.get('HERO_MOTION', 'walk')
assert MOTION in ('walk', 'run')
LOG_STEM = 'hero' if MOTION == 'walk' else 'hero-run'
def bounds(obj):
    deps = bpy.context.evaluated_depsgraph_get()
    evaluated = obj.evaluated_get(deps)
    mesh = evaluated.to_mesh()
    coords = np.array([(evaluated.matrix_world @ v.co)[:] for v in mesh.vertices])
    evaluated.to_mesh_clear()
    assert np.isfinite(coords).all()
    return np.array([coords.min(0), coords.max(0)])

bpy.ops.wm.open_mainfile(filepath=str(ROOT/f'outputs/hero-{MOTION}.blend'))
expected = []
end_frame=91 if 'loop_displacement' in bpy.data.objects['HeroRig'] else 90
for f in (1,46,end_frame):
    bpy.context.scene.frame_set(f)
    expected.append(bounds(bpy.data.objects['InkHero']))
for o in list(bpy.data.objects):
    bpy.data.objects.remove(o, do_unlink=True)
for a in list(bpy.data.actions):
    bpy.data.actions.remove(a)
bpy.context.scene.render.fps = 30
bpy.ops.import_scene.gltf(filepath=str(ROOT/f'outputs/hero-{MOTION}.glb'))
hero = next(o for o in bpy.context.scene.objects if o.type=='MESH')
rig = next(o for o in bpy.context.scene.objects if o.type=='ARMATURE')
assert len(rig.data.bones)==16
assert rig.animation_data and rig.animation_data.action
start, end = rig.animation_data.action.frame_range
actual = []
for f in (start, start+45, end):
    bpy.context.scene.frame_set(int(round(f)))
    actual.append(bounds(hero))
errors = [float(np.abs(a-b).max()) for a,b in zip(expected, actual)]
assert max(errors)<.005, f'GLB round-trip animation mismatch: {errors}'
assert np.abs(actual[0]-actual[1]).max()>.01
report = {'status':'PASS','glb_bones':len(rig.data.bones),
          'imported_action_start_frame':float(start),'imported_action_end_frame':float(end),
          'max_animated_bounds_difference_m':max(errors),
          'sample_bounds_differences_m':errors,
          'notes':'Checks re-imported skinned animation at start, middle and end; GLB keeps top four weights.'}
(ROOT/f'docs/logs/{LOG_STEM}-glb-check.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report,indent=2))

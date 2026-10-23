import bpy,json,numpy as np
from pathlib import Path
R=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(R/'outputs/tripo-pixel-cloth-test.blend'))
hero=bpy.data.objects['TripoPixel_Working'];keys=hero.data.shape_keys.key_blocks
assert len(keys)==152
checks=[]
for f in [31,75,76,90,120,150]:
    bpy.context.scene.frame_set(f)
    ev=hero.evaluated_get(bpy.context.evaluated_depsgraph_get())
    actual=np.array([v.co[:] for v in ev.data.vertices])
    expected=np.array([v.co[:] for v in keys[f'Physical bake {f:03d}'].data])
    error=float(np.abs(actual-expected).max());assert error<1e-6
    checks.append({'frame':f,'max_replay_error':error})
d=json.loads((R/'docs/logs/tripo-pixel-cloth.json').read_text())
tip=np.array([m['scarf_tip'] for m in d['metrics']]);hem=np.array([m['robe_hem'] for m in d['metrics']])
report={'replay_checks':checks,'scarf_post_stop_travel_m':float(np.linalg.norm(np.diff(tip[75:105],axis=0),axis=1).sum()),'robe_hem_post_stop_travel_m':float(np.linalg.norm(np.diff(hem[75:105],axis=0),axis=1).sum()),'max_skin_displacement_m':max(m['max_skin_displacement'] for m in d['metrics']),'quality_pass':False,'remaining':'Scarf collapses behind body; rough robe slit deformation; full garment collision and running rig not verified'}
(R/'docs/logs/tripo-pixel-cloth-verification.json').write_text(json.dumps(report,indent=2))
print(json.dumps(report))

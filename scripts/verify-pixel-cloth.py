import bpy,json,numpy as np,os
from pathlib import Path
R=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(R/os.environ.get('CLOTH_VERIFY_INPUT','outputs/tripo-pixel-cloth-test.blend')))
hero=bpy.data.objects['TripoPixel_Working'];keys=hero.data.shape_keys.key_blocks
assert len(keys)==152
checks=[]
rest=np.array([v.co[:] for v in keys[0].data]);x,y,z=rest.T
u=np.clip((.50-z)/.245,0,1)
radius=np.sqrt((x/(.091+.075*u))**2+(y/(.074+.041*u))**2)
colors=np.load(R/'outputs/tripo-pixel-inspection.npz')['colors']
robe=(radius>.60)&(radius<1.5)&(z>.215)&(z<.50)&((colors[:,2]-colors[:,0])<.08)
edges=np.array([e.vertices[:] for e in hero.data.edges])
edges=edges[np.all(robe[edges],axis=1)]
length=np.linalg.norm(rest[edges[:,0]]-rest[edges[:,1]],axis=1)
edges=edges[length>1e-5];length=length[length>1e-5]
for f in [31,75,76,90,120,150]:
    bpy.context.scene.frame_set(f)
    ev=hero.evaluated_get(bpy.context.evaluated_depsgraph_get())
    actual=np.array([v.co[:] for v in ev.data.vertices])
    expected=np.array([v.co[:] for v in keys[f'Physical bake {f:03d}'].data])
    error=float(np.abs(actual-expected).max());assert error<1e-6
    stretch=np.linalg.norm(actual[edges[:,0]]-actual[edges[:,1]],axis=1)/length
    worst=edges[np.argsort(stretch)[-5:]]
    checks.append({'frame':f,'max_replay_error':error,'robe_edge_stretch_p95':float(np.percentile(stretch,95)),'robe_edge_stretch_max':float(stretch.max()),'robe_edges_over_2x':int((stretch>2).sum()),'worst_edge_rest_positions':rest[worst].tolist()})
d=json.loads((R/'docs/logs/tripo-pixel-cloth.json').read_text())
tip=np.array([m['scarf_tip'] for m in d['metrics']]);hem=np.array([m['robe_hem'] for m in d['metrics']])
report={'replay_checks':checks,'scarf_post_stop_travel_m':float(np.linalg.norm(np.diff(tip[75:105],axis=0),axis=1).sum()),'robe_hem_post_stop_travel_m':float(np.linalg.norm(np.diff(hem[75:105],axis=0),axis=1).sum()),'max_skin_displacement_m':max(m['max_skin_displacement'] for m in d['metrics']),'quality_pass':False,'remaining':'Full garment collision and running rig not verified; do not equate reduced edge stretch with final art approval'}
(R/os.environ.get('CLOTH_VERIFY_REPORT','docs/logs/tripo-pixel-cloth-verification.json')).write_text(json.dumps(report,indent=2))
print(json.dumps(report))

"""Compare retimed poses against the approved source at matching phases."""
import bpy,json,subprocess
import numpy as np
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
BASE='6840495926913b804608ec6f184b89587a9368cc'
before=ROOT/'.cache/hero-run-speed-before.blend'
if not before.exists():
    before.write_bytes(subprocess.check_output(['git','show',BASE+':outputs/hero-run.blend'],cwd=ROOT))
bpy.ops.wm.open_mainfile(filepath=str(before))
s=bpy.context.scene;r=bpy.data.objects['HeroRig'];oldtravel=np.array(r['loop_displacement'])
rest=np.array([v.co[:] for v in bpy.data.objects['InkHero'].data.vertices])
bind=np.array([np.array(b.matrix_local) for b in r.data.bones])
expected=[]
for f in range(1,46):
    s.frame_set(f);expected.append([b.rotation_quaternion.copy() for b in r.pose.bones])
bpy.ops.wm.open_mainfile(filepath=str(ROOT/'outputs/hero-run.blend'))
s=bpy.context.scene;r=bpy.data.objects['HeroRig'];error=0
for i in range(91):
    phase=(i*1.5)%45;a=int(phase);t=phase-a
    s.frame_set(i+1)
    for j,b in enumerate(r.pose.bones):
        q=expected[a][j].slerp(expected[(a+1)%45][j],t)
        error=max(error,float(np.abs(np.array(q)-np.array(b.rotation_quaternion)).max()))
mesh_error=float(np.abs(rest-np.array([v.co[:] for v in bpy.data.objects['InkHero'].data.vertices])).max())
bind_error=float(np.abs(bind-np.array([np.array(b.matrix_local) for b in r.data.bones])).max())
travel_error=float(np.abs(np.array(r['loop_displacement'])-oldtravel*1.5).max())
assert error<1e-6 and mesh_error<1e-7 and bind_error<1e-7 and travel_error<1e-6
assert s.render.fps==30 and s.frame_end==90 and r['run_cycle_seconds']==.5
report={'status':'PASS','baseline_commit':BASE,'frames':91,'rate':1.5,'cycle_seconds':.5,'cycles_in_3_seconds':6,'max_quaternion_difference_from_phase_matched_source':error,'rest_vertex_difference_m':mesh_error,'bind_matrix_difference':bind_error,'travel_scaling_error_m':travel_error,'scope':'Preserved approved poses under periodic slerp; ground lift, contact and loop verified separately.'}
(ROOT/'docs/logs/hero-run-timing-check.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report,indent=2))

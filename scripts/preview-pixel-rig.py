"""Saved-rig verification and diagnostic joint-test render, not generated running."""
import bpy, json
import numpy as np
from pathlib import Path
R=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(R/'outputs/tripo-pixel-rig.blend'))
s=bpy.context.scene;rig=bpy.data.objects['TripoPixel_Rig'];hero=bpy.data.objects['TripoPixel_Character']
out=R/'.cache/pixel-rig';out.mkdir(parents=True,exist_ok=True)
s.render.resolution_x=s.render.resolution_y=384;s.cycles.samples=8
length_error=0;scale_error=0
for f in range(1,82):
 s.frame_set(f);bpy.context.view_layer.update()
 for b in rig.pose.bones:
  length_error=max(length_error,abs((b.tail-b.head).length-b.bone.length))
  scale_error=max(scale_error,max(abs(x-1) for x in b.scale))
 ev=hero.evaluated_get(bpy.context.evaluated_depsgraph_get())
 assert np.isfinite(np.array([v.co[:] for v in ev.data.vertices])).all()
 s.render.filepath=str(out/f'{f:04d}.png');bpy.ops.render.render(write_still=True)
assert length_error<1e-6 and scale_error==0
(R/'docs/logs/pixel-rig-replay.json').write_text(json.dumps({'saved_file_reopened':True,'frames':81,'max_length_error_m':length_error,'max_scale_error':scale_error,'finite_mesh_all_frames':True},indent=2))

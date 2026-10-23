"""Reopen the saved cloth bake, check replay, and render the complete 3-second clip."""
import bpy, numpy as np, json
from pathlib import Path
R=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(R/'outputs/pixel-run-cloth.blend'))
s=bpy.context.scene;h=bpy.data.objects['TripoPixel_Character']
cache=np.load(R/'outputs/pixel-run-cloth-cache.npz')['positions']
folder=R/'.cache/pixel-run-preview';folder.mkdir(parents=True,exist_ok=True)
error=0.
for f in range(1,91):
 s.frame_set(f);bpy.context.view_layer.update()
 q=np.array([v.co[:] for v in h.evaluated_get(bpy.context.evaluated_depsgraph_get()).data.vertices])
 error=max(error,float(np.abs(q-cache[f-1]).max()));assert np.isfinite(q).all()
 s.render.filepath=str(folder/f'{f:04d}.png');bpy.ops.render.render(write_still=True)
assert error<1e-5
(R/'docs/logs/pixel-run-replay.json').write_text(json.dumps({'frames':90,'fps':s.render.fps,'saved_bake_max_error_m':error},indent=2))

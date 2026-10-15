"""Render the rebuilt neutral model and its independent joint-test clip."""
import bpy,json
from pathlib import Path
from mathutils import Vector
ROOT=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(ROOT/'outputs/hero-model.blend'))
s=bpy.context.scene;c=s.camera;s.render.resolution_x=s.render.resolution_y=512;s.cycles.samples=16
prefs=bpy.context.preferences.addons['cycles'].preferences;prefs.compute_device_type='CUDA';prefs.get_devices()
for d in prefs.devices:d.use=d.type=='CUDA'
s.cycles.device='GPU';dest=ROOT/'.cache/hero-model-frames';dest.mkdir(parents=True,exist_ok=True)
for f in range(1,121):
    s.frame_set(f);s.render.filepath=str(dest/f'{f:03d}.png');bpy.ops.render.render(write_still=True)
print('MODEL_JOINT_TEST_RENDERED_120_FRAMES')

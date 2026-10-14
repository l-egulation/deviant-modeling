"""Render the saved Blender walk as 90 PNG frames for a 3-second preview."""
import bpy
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(ROOT/'outputs/hero-walk.blend'))
scene = bpy.context.scene
# Merge the bone action and object translation into one complete walk clip.
bpy.ops.object.select_all(action='DESELECT')
for name in ('InkHero','HeroRig'):
    bpy.data.objects[name].select_set(True)
bpy.context.view_layer.objects.active = bpy.data.objects['HeroRig']
bpy.ops.export_scene.gltf(filepath=str(ROOT/'outputs/hero-walk.glb'), use_selection=True,
                          export_animations=True, export_frame_range=True,
                          export_force_sampling=True, export_animation_mode='SCENE')
prefs = bpy.context.preferences.addons['cycles'].preferences
prefs.compute_device_type = 'CUDA'
prefs.get_devices()
for d in prefs.devices:
    d.use = d.type == 'CUDA'
scene.cycles.device = 'GPU' if any(d.type == 'CUDA' for d in prefs.devices) else 'CPU'
dest = ROOT/'.cache/hero-frames'
dest.mkdir(parents=True, exist_ok=True)
for f in range(1, 91):
    scene.frame_set(f)
    scene.render.filepath = str(dest/f'{f:03d}.png')
    bpy.ops.render.render(write_still=True)

"""Render the saved Blender walk as 90 PNG frames for a 3-second preview."""
import os
import bpy
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MOTION = os.environ.get('HERO_MOTION', 'walk')
assert MOTION in ('walk', 'run')
LOG_STEM = 'hero' if MOTION == 'walk' else 'hero-run'
bpy.ops.wm.open_mainfile(filepath=str(ROOT/f'outputs/hero-{MOTION}.blend'))
scene = bpy.context.scene
# Merge the bone action and object translation into one complete walk clip.
bpy.ops.object.select_all(action='DESELECT')
for name in ('InkHero','HeroRig'):
    bpy.data.objects[name].select_set(True)
bpy.context.view_layer.objects.active = bpy.data.objects['HeroRig']
scene.frame_end=91 if 'loop_displacement' in bpy.data.objects['HeroRig'] else 90
bpy.ops.export_scene.gltf(filepath=str(ROOT/f'outputs/hero-{MOTION}.glb'), use_selection=True,
                          export_animations=True, export_frame_range=True,
                          export_force_sampling=True, export_animation_mode='SCENE',
                          export_anim_slide_to_zero=MOTION == 'run')
scene.frame_end=90
prefs = bpy.context.preferences.addons['cycles'].preferences
prefs.compute_device_type = 'CUDA'
prefs.get_devices()
for d in prefs.devices:
    d.use = d.type == 'CUDA'
scene.cycles.device = 'GPU' if any(d.type == 'CUDA' for d in prefs.devices) else 'CPU'
dest = ROOT/('.cache/hero-frames' if MOTION == 'walk' else '.cache/hero-run-frames')
dest.mkdir(parents=True, exist_ok=True)
for f in range(1, 92 if MOTION == 'run' else 91):
    scene.frame_set(f)
    scene.render.filepath = str(dest/f'{f:03d}.png')
    bpy.ops.render.render(write_still=True)

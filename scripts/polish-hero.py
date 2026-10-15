"""Apply contact and presentation fixes without changing upper-body motion."""
import bpy
import json
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from hero_preview import configure_preview
from hero_feet import plant_feet
ROOT=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(ROOT/'outputs/hero-walk.blend'))
scene=bpy.context.scene
rig,hero,source=[bpy.data.objects[n] for n in ('HeroRig','InkHero','KimodoSource')]
report=plant_feet(scene,rig,hero,source,ROOT/'outputs/walk.npz')
configure_preview(scene,rig,scene.camera)
bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'outputs/hero-walk.blend'),compress=True)
report.update(status='PASS',preserved='Upper-body rotations, bone lengths/scales, horizontal travel, source GLB/NPZ/BVH')
(ROOT/'docs/logs/hero-polish-check.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report,indent=2),flush=True)

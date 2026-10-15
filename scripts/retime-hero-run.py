"""Apply the timing stage to an existing approved, unretimed run Blend."""
import bpy,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
from hero_timing import accelerate_run
from hero_preview import configure_preview
bpy.ops.wm.open_mainfile(filepath=str(ROOT/'outputs/hero-run.blend'))
s=bpy.context.scene;r=bpy.data.objects['HeroRig']
report=accelerate_run(s,r,bpy.data.objects['InkHero'])
configure_preview(s,r,s.camera)
bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'outputs/hero-run.blend'),compress=True)
(ROOT/'docs/logs/hero-run-timing.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report,indent=2))

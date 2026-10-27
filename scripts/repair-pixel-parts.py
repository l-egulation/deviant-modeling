import bpy,json,sys
from pathlib import Path
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'scripts'))
from pixel_local_repair import repair
report={}
for old,new in [('pixel-readable-idle','pixel-repaired-idle'),('pixel-run','pixel-repaired-run')]:
 bpy.ops.wm.open_mainfile(filepath=str(R/f'outputs/{old}.blend'))
 obj=bpy.data.objects['TripoPixel_Character'];rig=bpy.data.objects['TripoPixel_Rig']
 report[new]=repair(obj,rig);assert report[new]['hood_max_displacement_m']==0
 bpy.ops.wm.save_as_mainfile(filepath=str(R/f'outputs/{new}.blend'),compress=True)
(R/'docs/logs/pixel-local-repair.json').write_text(json.dumps(report,indent=2));print(json.dumps(report))

"""Capture the current running cycle at 30 fps with stable framing and alpha."""
import bpy,json
from pathlib import Path
from mathutils import Vector
from bpy_extras.object_utils import world_to_camera_view
R=Path(__file__).resolve().parents[1];out=R/'outputs/hero-run-capture';(out/'frames').mkdir(parents=True,exist_ok=True)
bpy.ops.wm.open_mainfile(filepath=str(R/'outputs/hero-mixamo-run.blend'))
s=bpy.context.scene;r=bpy.data.objects['TripoRunRig'];c=s.camera;c.animation_data_clear()
s.render.fps=30;s.render.film_transparent=True;s.render.image_settings.file_format='PNG';s.render.image_settings.color_mode='RGBA';s.render.resolution_x=s.render.resolution_y=512;s.render.resolution_percentage=100
c.data.type='ORTHO';c.data.ortho_scale=1.4;offset=Vector((2.7,0,.10));c.rotation_euler=(-offset).to_track_quat('-Z','Y').to_euler()
rows=[]
for i in range(22):
 s.frame_set(i+1);center=Vector((r.location.x,r.location.y,.49));c.location=center+offset;bpy.context.view_layer.update()
 s.render.filepath=str(out/f'frames/{i:03d}.png');bpy.ops.render.render(write_still=True)
 ground=world_to_camera_view(s,c,Vector((r.location.x,r.location.y,0)))
 rows.append({'file':f'frames/{i:03d}.png','source_frame':i+1,'time_seconds':i/30,'ground_pivot_pixels':[ground.x*512,(1-ground.y)*512]})
meta={'source_blend':'outputs/hero-mixamo-run.blend','source_commit':'51d27fe','motion':'Mixamo with approved elbow/root corrections, not Kimodo','fps':30,'frame_count':22,'cycle_seconds':22/30,'canvas':[512,512],'background':'transparent RGBA','view':'orthographic side, left-facing; fixed orientation/height, root XY tracking only','pixel_art':False,'crop':'shared full canvas, no per-frame auto-crop','sheet':{'file':'spritesheet.png','columns':6,'rows':4,'cell':[512,512],'order':'left to right, top to bottom; final two cells empty'},'frames':rows}
(out/'capture.json').write_text(json.dumps(meta,indent=2)+'\n')

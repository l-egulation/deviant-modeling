import bpy,json
from pathlib import Path
from mathutils import Vector
R=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(R/'outputs/tripo-pixel-cloth-test.blend'))
s=bpy.context.scene;c=s.camera;center=Vector((0,.035,.80))
c.location=center+Vector((3,0,0));c.rotation_euler=(center-c.location).to_track_quat('-Z','Y').to_euler();c.data.ortho_scale=.50
s.render.resolution_x=s.render.resolution_y=384
metrics=json.loads((R/'docs/logs/tripo-pixel-cloth.json').read_text())['metrics']
peak=max(metrics[75:105],key=lambda m:abs(m['hood_pitch_degrees']))['frame']
for frame,label in [(75,'before-stop'),(peak,'reaction'),(105,'settled')]:
    s.frame_set(frame);s.render.filepath=str(R/f'outputs/hood-{label}.png');bpy.ops.render.render(write_still=True)
print('Hood close-up frames',75,peak,105)

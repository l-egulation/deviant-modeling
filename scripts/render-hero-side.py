"""Render a fixed side view for small-resolution silhouette review."""
import bpy,json,math
from pathlib import Path
from mathutils import Vector
ROOT=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(ROOT/'outputs/hero-run.blend'))
s=bpy.context.scene;r=bpy.data.objects['HeroRig'];c=s.camera
travel=Vector(r['loop_displacement'])
locations=[]
for f in range(1,47):
    s.frame_set(f);locations.append(r.location.copy()-travel*((f-1)/90))
r.animation_data.action=r.animation_data.action.copy()
for f,location in enumerate(locations,1):
    s.frame_set(f);r.location=location;r.keyframe_insert('location',frame=f)
c.animation_data_clear();c.location=(-3,0,.49);c.rotation_euler=Vector((1,0,0)).to_track_quat('-Z','Y').to_euler();c.data.type='ORTHO';c.data.ortho_scale=1.20
s.frame_set(1)
for o in s.objects:
    if o.type=='LIGHT':
        position=o.location.copy();o.animation_data_clear();o.location=position
bpy.data.objects['StudioFloor'].hide_render=True
s.render.film_transparent=True;s.render.resolution_x=s.render.resolution_y=384;s.render.resolution_percentage=100
s.render.image_settings.file_format='PNG';s.render.image_settings.color_mode='RGBA'
prefs=bpy.context.preferences.addons['cycles'].preferences;prefs.compute_device_type='CUDA';prefs.get_devices()
for d in prefs.devices:d.use=d.type=='CUDA'
s.cycles.device='GPU';s.cycles.samples=32
s.frame_start=1;s.frame_end=45;s.render.fps=30
out=ROOT/'.cache/hero-run-side-frames';out.mkdir(exist_ok=True)
angles=[]
for f in range(1,47):
    s.frame_set(f);s.render.filepath=str(out/f'{f:03d}.png');bpy.ops.render.render(write_still=True)
    if f<=45:
        b=r.pose.bones['Head'];delta=b.matrix.to_3x3() @ b.bone.matrix_local.to_3x3().inverted()
        front=delta @ Vector((0,-1,0));angles.append(math.degrees(math.atan2(front.x,-front.y)))
facing={'head_front_yaw_min_degrees':min(angles),'head_front_yaw_max_degrees':max(angles),'head_yaw_excursion_degrees':max(angles)-min(angles),'scope':'Measured head-facing variation; not a numeric pass/fail quality threshold.'}
(ROOT/'docs/logs/hero-run-side-facing.json').write_text(json.dumps(facing,indent=2)+'\n')
print('SIDE_RENDER_COMPLETE: 45 frames plus loop endpoint, fixed orthographic camera, linear travel removed')

"""Import the downloaded Mixamo default character and render its untouched run."""
import bpy,json,os,numpy as np
from pathlib import Path
from mathutils import Vector
ROOT=Path(__file__).resolve().parents[1]
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.fbx(filepath=str(ROOT/'assets/mixamo-running.fbx'))
scene=bpy.context.scene
rig=next(o for o in scene.objects if o.type=='ARMATURE')
meshes=[o for o in scene.objects if o.type=='MESH']
action=rig.animation_data.action
start,end=[round(x) for x in action.frame_range]
scene.render.fps=30;scene.frame_start=start;scene.frame_end=end;scene.frame_set(start)
def bone(suffix):return next(b for b in rig.pose.bones if b.name.endswith(suffix))
first=rig.matrix_world@bone('Hips').head
forward=Vector((0,0,0))
for side in ('Left','Right'):
    forward+=rig.matrix_world.to_3x3()@(bone(side+'ToeBase').head-bone(side+'Foot').head)
forward.z=0;forward.normalize();side=Vector((forward.y,-forward.x,0))
points=[o.matrix_world@Vector(c) for o in meshes for c in o.bound_box]
lo=Vector([min(p[i] for p in points) for i in range(3)])
hi=Vector([max(p[i] for p in points) for i in range(3)])
height=hi.z-lo.z
scene.frame_set(end);last=rig.matrix_world@bone('Hips').head
scene.world=bpy.data.worlds.new('Studio');scene.world.use_nodes=True
scene.world.node_tree.nodes['Background'].inputs[0].default_value=(.65,.68,.72,1)
scene.world.node_tree.nodes['Background'].inputs[1].default_value=.8
bpy.ops.mesh.primitive_plane_add(size=200,location=(0,0,lo.z-.005))
floor=bpy.context.object;mat=bpy.data.materials.new('Floor');mat.diffuse_color=(.32,.35,.39,1);floor.data.materials.append(mat)
for pos,power in [((3,-4,5),400),((-3,2,4),250)]:
    bpy.ops.object.light_add(type='AREA',location=pos);light=bpy.context.object;light.data.energy=power;light.data.size=4
    light.rotation_euler=(Vector((0,0,height/2))-light.location).to_track_quat('-Z','Y').to_euler()
bpy.ops.object.camera_add();camera=bpy.context.object;scene.camera=camera;camera.data.type='ORTHO';camera.data.ortho_scale=height*1.25
scene.render.engine='CYCLES';scene.cycles.samples=16;scene.cycles.use_denoising=True
prefs=bpy.context.preferences.addons['cycles'].preferences;prefs.compute_device_type='CUDA';prefs.get_devices()
for d in prefs.devices:d.use=d.type=='CUDA'
scene.cycles.device='GPU';scene.render.resolution_x=scene.render.resolution_y=512;scene.render.resolution_percentage=100
scene.view_settings.view_transform='Standard';scene.render.image_settings.file_format='PNG'
dest=ROOT/'.cache/mixamo-run';dest.mkdir(parents=True,exist_ok=True)
for label,offset in [('side',side*height*3+Vector((0,0,height*.05))),('three-quarter',(side*.75+forward*.7)*height*3+Vector((0,0,height*.12)))]:
    for f in range(start,end+1):
        scene.frame_set(f);t=(f-start)/max(1,end-start)
        center=first.lerp(last,t);center.z=lo.z+height*.49
        camera.location=center+offset;camera.rotation_euler=(-offset).to_track_quat('-Z','Y').to_euler()
        camera.keyframe_insert('location',frame=f);camera.keyframe_insert('rotation_euler',frame=f)
        scene.render.filepath=str(dest/f'{label}-{f-start:03d}.png')
        if os.environ.get('MIXAMO_RENDER','1')=='1':bpy.ops.render.render(write_still=True)
scene.frame_set(start)
bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'outputs/mixamo-running.blend'),compress=True)
report={'source':'Mixamo Running / Running With Intention, default character','original_file':'assets/mixamo-running.fbx',
        'frame_start':start,'frame_end':end,'frames':end-start+1,'fps':30,'bones':len(rig.data.bones),
        'mesh_objects':len(meshes),'height_m':height,'motion_pose_edits':False,'timing_edits':False,
        'download_options':'FBX Binary, With Skin, 30fps, keyframe reduction none; default Overdrive 50 and Arm-Space 50; In Place off'}
(ROOT/'docs/logs/mixamo-running.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report))

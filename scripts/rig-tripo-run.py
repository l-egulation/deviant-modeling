"""Fit the actual Tripo T-pose export and transfer existing Kimodo run motion."""
import bpy
import json
import sys
import os
import numpy as np
from pathlib import Path
from mathutils import Vector

ROOT = Path(__file__).resolve().parents[1]
MOTION_PATH=ROOT/os.environ.get('TRIPO_MOTION','outputs/tripo-run-source.bvh')
CONTACT_PATH=ROOT/os.environ.get('TRIPO_CONTACTS','outputs/tripo-run-contact.npz')
sys.path.insert(0, str(ROOT/'scripts'))
from retarget import retarget_rotation
from hero_feet import plant_feet
from hero_preview import configure_preview, boot_rotation

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=str(ROOT/'assets/ink-hero-tpose.glb'))
hero = next(o for o in bpy.context.scene.objects if o.type == 'MESH')
hero.name = 'TripoHero'
bpy.context.view_layer.objects.active = hero
bpy.ops.object.transform_apply(location=True,rotation=True,scale=True)
original = np.array([v.co[:] for v in hero.data.vertices])
spec = {'Hips':((0,.015,.35),(0,.015,.41),None),
        'Spine1':((0,.015,.41),(0,.015,.48),'Hips'),
        'Chest':((0,.015,.48),(0,.015,.60),'Spine1'),
        'Head':((0,.015,.60),(0,.015,.94),'Chest')}
for side,sign in [('Left',1),('Right',-1)]:
    spec.update({side+'Clavicle':((sign*.025,.0,.55),(sign*.135,.0,.55),'Chest'),
                 side+'Arm':((sign*.135,0,.55),(sign*.265,0,.55),side+'Clavicle'),
                 side+'ForeArm':((sign*.265,0,.55),(sign*.395,0,.55),side+'Arm'),
                 side+'Hand':((sign*.395,0,.55),(sign*.46,0,.55),side+'ForeArm'),
                 side+'UpLeg':((sign*.077,.015,.35),(sign*.112,.02,.225),'Hips'),
                 side+'Leg':((sign*.112,.02,.225),(sign*.15,.025,.092),side+'UpLeg'),
                 side+'Foot':((sign*.15,.025,.092),(sign*.15,-.10,.038),side+'Leg')})
data = bpy.data.armatures.new('TripoRunRig')
rig = bpy.data.objects.new('TripoRunRig',data)
bpy.context.collection.objects.link(rig)
bpy.context.view_layer.objects.active=rig
bpy.ops.object.mode_set(mode='EDIT')
for n,(h,t,p) in spec.items():
    b=data.edit_bones.new(n);b.head=h;b.tail=t
    if p:b.parent=data.edit_bones[p]
bpy.ops.object.mode_set(mode='OBJECT')
rig.show_in_front=True

# Continuous anatomical weights avoid heat leakage between the touching hood,
# collar and sleeve shells. The exported mesh/UVs stay exactly unchanged.
def smooth(a,b,value):
    t=max(0,min(1,(value-a)/(b-a)))
    return t*t*(3-2*t)
def blend(a,b,t):
    result={n:w*(1-t) for n,w in a.items()}
    for n,w in b.items():result[n]=result.get(n,0)+w*t
    return result
for n in spec:hero.vertex_groups.new(name=n)
heat_unweighted=0
for v in hero.data.vertices:
    x,y,z=v.co;ax=abs(x);side='Left' if x>=0 else 'Right'
    body=blend({'Hips':1},{'Spine1':1},smooth(.36,.43,z))
    body=blend(body,{'Chest':1},smooth(.43,.50,z))
    body=blend(body,{'Head':1},smooth(.62,.68,z))
    arm=blend({side+'Clavicle':1},{side+'Arm':1},smooth(.115,.205,ax))
    arm=blend(arm,{side+'ForeArm':1},smooth(.215,.31,ax))
    arm=blend(arm,{side+'Hand':1},smooth(.35,.403,ax))
    amount=smooth(.105,.20,ax)*smooth(.43,.49,z)*(1-smooth(.585,.645,z))
    weights=blend(body,arm,amount)
    legs=[]
    for leg_side in ('Right','Left'):
        leg=blend({leg_side+'Foot':1},{leg_side+'Leg':1},smooth(.105,.165,z))
        leg=blend(leg,{leg_side+'UpLeg':1},smooth(.16,.29,z))
        legs.append(leg)
    leg=blend(legs[0],legs[1],smooth(-.05,.05,x))
    weights=blend(leg,weights,smooth(.30,.38,z))
    for n,w in weights.items():
        if w>1e-7:hero.vertex_groups[n].add([v.index],w,'REPLACE')
hero.parent=rig
mod=hero.modifiers.new('Character skin','ARMATURE');mod.object=rig;mod.use_deform_preserve_volume=False
for p in hero.data.polygons:p.use_smooth=True

bpy.ops.import_anim.bvh(filepath=str(MOTION_PATH),global_scale=.01,
                        axis_forward='-Z',axis_up='Y',frame_start=1,
                        update_scene_fps=True,update_scene_duration=True)
source=bpy.context.object;source.name='KimodoSource';source.hide_render=True;source.hide_set(True)
scene=bpy.context.scene;scene.frame_start=1;scene.frame_end=90;scene.render.fps=30
rest={n:data.bones[n].matrix_local.copy() for n in spec}
rel={n:rest[p].inverted()@rest[n] if p else rest[n] for n,(_,_,p) in spec.items()}
mapping={n:(n.replace('Clavicle','Shoulder') if 'Clavicle' in n else
            n.replace('UpLeg','Leg') if 'UpLeg' in n else
            n.replace('Leg','Shin') if n.endswith('Leg') else n) for n in spec}
reference={n:source.data.bones[mapping[n]].matrix_local.to_3x3() for n in spec}
# Unspread the resting legs into the source's stance; lengths remain fitted.
for side in ('Left','Right'):
    n=side+'UpLeg'
    correction=reference[n].col[1].normalized().rotation_difference(rest[n].to_3x3().col[1].normalized()).to_matrix()
    for suffix in ('UpLeg','Leg'):
        reference[side+suffix]=correction@reference[side+suffix]
scale=sum(data.bones['Left'+n].length for n in ('UpLeg','Leg'))/sum(source.data.bones[n].length for n in ('LeftLeg','LeftShin'))
for f in range(1,91):
    scene.frame_set(f);desired={}
    for n,(_,_,parent) in spec.items():
        world=retarget_rotation(source.pose.bones[mapping[n]].matrix.to_3x3().normalized(),reference[n],rest[n].to_3x3())
        if n.endswith('Foot'):world=boot_rotation(world,rest[n].to_3x3(),30)
        desired[n]=world
        local=desired[parent].inverted()@world if parent else world
        q=(rel[n].to_3x3().inverted()@local).to_quaternion()
        pb=rig.pose.bones[n];pb.rotation_mode='QUATERNION';q.make_compatible(pb.rotation_quaternion)
        pb.rotation_quaternion=q;pb.keyframe_insert('rotation_quaternion',frame=f)
    root=source.pose.bones['Hips'].head.copy()
    if f==1:first=root.copy()
    rig.location=(root-first)*scale;rig.keyframe_insert('location',frame=f)
contact=plant_feet(scene,rig,hero,source,CONTACT_PATH,allow_flight=True,swing_iterations=128)

# Fixed orientation and constant travel prevent the camera following pelvis bob.
bpy.ops.object.camera_add();camera=bpy.context.object;scene.camera=camera
camera.data.type='ORTHO';camera.data.ortho_scale=1.4
scene.world=bpy.data.worlds.new('StudioWorld');scene.world.use_nodes=True
scene.world.node_tree.nodes['Background'].inputs[0].default_value=(.6,.6,.6,1)
scene.world.node_tree.nodes['Background'].inputs[1].default_value=.8
configure_preview(scene,rig,camera)
# Present this fresh generation in a strict side view with linear tracking.
camera.animation_data_clear()
for f in (1,90):
    scene.frame_set(f);center=Vector((rig.location.x,rig.location.y,.49))
    camera.location=center+Vector((2.7,0,.10))
    camera.rotation_euler=Vector((-2.7,0,-.10)).to_track_quat('-Z','Y').to_euler()
    camera.keyframe_insert('location',frame=f);camera.keyframe_insert('rotation_euler',frame=f)
for layer in camera.animation_data.action.layers:
    for strip in layer.strips:
        for bag in strip.channelbags:
            for curve in bag.fcurves:
                for point in curve.keyframe_points:point.interpolation='LINEAR'
scene.render.engine='CYCLES';scene.cycles.samples=16;scene.cycles.use_denoising=True
prefs=bpy.context.preferences.addons['cycles'].preferences;prefs.compute_device_type='CUDA';prefs.get_devices()
for d in prefs.devices:d.use=d.type=='CUDA'
scene.cycles.device='GPU'
scene.view_settings.view_transform='Standard'
scene.render.resolution_x=scene.render.resolution_y=512;scene.render.resolution_percentage=100
scene.render.image_settings.file_format='PNG';scene.frame_set(1)
bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'outputs/tripo-run.blend'),compress=True)
bpy.ops.object.select_all(action='DESELECT');hero.select_set(True);rig.select_set(True);bpy.context.view_layer.objects.active=rig
bpy.ops.export_scene.gltf(filepath=str(ROOT/'outputs/tripo-run.glb'),use_selection=True,
    export_animations=True,export_frame_range=True,export_force_sampling=True,export_animation_mode='SCENE')
report={'source':'assets/ink-hero-tpose.glb','motion':str(MOTION_PATH.relative_to(ROOT)),
        'bones':len(data.bones),'vertices':len(hero.data.vertices),'weighting':'continuous anatomical regions; no heat solver',
        'rest_vertex_error':float(np.max(np.abs(original-np.array([v.co[:] for v in hero.data.vertices])))),
        'contact':contact,'source_mapping':mapping,'status':'BUILT; visual verification pending'}
(ROOT/'docs/logs/tripo-run-rig.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report))

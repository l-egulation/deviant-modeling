"""Fit a rest rig to the approved A model without changing its geometry."""
import bpy
import json
import numpy as np
from pathlib import Path
from mathutils import Vector

ROOT = Path(__file__).resolve().parents[1]
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=str(ROOT/'outputs/hero-proportion-model.glb'))
hero = next(o for o in bpy.context.scene.objects if o.type == 'MESH')
hero.name = 'TripoHero'
bpy.context.view_layer.objects.active = hero
bpy.ops.object.transform_apply(location=True,rotation=True,scale=True)
original = np.array([v.co[:] for v in hero.data.vertices])
spec = {'Hips':((0,.015,.34),(0,.015,.40),None),
        'Spine1':((0,.015,.40),(0,.015,.46),'Hips'),
        'Chest':((0,.015,.46),(0,.015,.60),'Spine1'),
        'Head':((0,.015,.60),(0,.015,.94),'Chest')}
for side,sign in [('Left',1),('Right',-1)]:
    spec.update({side+'Clavicle':((sign*.025,.0,.55),(sign*.125,.0,.55),'Chest'),
                 side+'Arm':((sign*.125,0,.55),(sign*.235,0,.55),side+'Clavicle'),
                 side+'ForeArm':((sign*.235,0,.55),(sign*.355,0,.55),side+'Arm'),
                 side+'Hand':((sign*.355,0,.55),(sign*.42,0,.55),side+'ForeArm'),
                 side+'UpLeg':((sign*.07,.015,.34),(sign*.10,.02,.215),'Hips'),
                 side+'Leg':((sign*.10,.02,.215),(sign*.13,.025,.075),side+'UpLeg'),
                 side+'Foot':((sign*.13,.025,.075),(sign*.13,-.10,.038),side+'Leg')})
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
    arm=blend({side+'Clavicle':1},{side+'Arm':1},smooth(.105,.175,ax))
    arm=blend(arm,{side+'ForeArm':1},smooth(.195,.275,ax))
    arm=blend(arm,{side+'Hand':1},smooth(.325,.375,ax))
    amount=smooth(.105,.20,ax)*smooth(.40,.46,z)*(1-smooth(.61,.65,z))
    weights=blend(body,arm,amount)
    legs=[]
    for leg_side in ('Right','Left'):
        leg=blend({leg_side+'Foot':1},{leg_side+'Leg':1},smooth(.09,.14,z))
        leg=blend(leg,{leg_side+'UpLeg':1},smooth(.16,.27,z))
        legs.append(leg)
    leg=blend(legs[0],legs[1],smooth(-.05,.05,x))
    weights=blend(leg,weights,smooth(.30,.38,z))
    for n,w in weights.items():
        if w>1e-7:hero.vertex_groups[n].add([v.index],w,'REPLACE')
# Guard against the observed sleeve-to-head leakage on the outer arms.
for v in hero.data.vertices:
    if abs(v.co.x)>.22 and .48<v.co.z<.60:
        leakage=sum(g.weight for g in v.groups if hero.vertex_groups[g.group].name in ('Head','Chest','Spine1','Hips'))
        assert leakage<1e-6, (v.index, leakage)
assert max(abs(sum(g.weight for g in v.groups)-1) for v in hero.data.vertices)<1e-5
hero.parent=rig
mod=hero.modifiers.new('Character skin','ARMATURE');mod.object=rig;mod.use_deform_preserve_volume=False
for p in hero.data.polygons:p.use_smooth=True


scene=bpy.context.scene
bpy.ops.object.camera_add();camera=bpy.context.object;scene.camera=camera
camera.data.type='ORTHO';camera.data.ortho_scale=1.4
scene.world=bpy.data.worlds.new('StudioWorld');scene.world.use_nodes=True
scene.world.node_tree.nodes['Background'].inputs[0].default_value=(.6,.6,.6,1)
scene.world.node_tree.nodes['Background'].inputs[1].default_value=.8
camera.location=(2.7,0,.59);camera.rotation_euler=Vector((-2.7,0,-.10)).to_track_quat('-Z','Y').to_euler()
scene.render.engine='CYCLES';scene.cycles.samples=16;scene.cycles.use_denoising=True
prefs=bpy.context.preferences.addons['cycles'].preferences;prefs.compute_device_type='CUDA';prefs.get_devices()
for d in prefs.devices:d.use=d.type=='CUDA'
scene.cycles.device='GPU';scene.view_settings.view_transform='Standard'
scene.render.resolution_x=scene.render.resolution_y=512;scene.render.resolution_percentage=100
scene.render.image_settings.file_format='PNG'
assert np.max(np.abs(original-np.array([v.co[:] for v in hero.data.vertices])))==0
bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'outputs/hero-proportion-rig.blend'),compress=True)
(ROOT/'docs/logs/hero-proportion-rig.json').write_text(json.dumps({'model':'outputs/hero-proportion-model.glb','rest_vertex_error':0,'bones':{n:{'head':h,'tail':t,'parent':p} for n,(h,t,p) in spec.items()},'scope':'Rest rig; motion and deformation checked separately'},indent=2)+'\n')

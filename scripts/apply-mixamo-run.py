"""Retarget the downloaded Mixamo run; preserve its upper-body motion and timing."""
import bpy,json,math,sys,numpy as np
from pathlib import Path
from mathutils import Vector,Quaternion
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'scripts'))
from hero_feet import plant_feet
from retarget import retarget_rotation
bpy.ops.wm.open_mainfile(filepath=str(ROOT/'outputs/tripo-run.blend'))
scene=bpy.context.scene;hero=bpy.data.objects['TripoHero'];rig=bpy.data.objects['TripoRunRig']
original=np.array([v.co[:] for v in hero.data.vertices]);rig.animation_data_clear();rig.location=(0,0,0)
for b in rig.pose.bones:b.rotation_quaternion=(1,0,0,0)
for o in list(scene.objects):
    if o.type=='ARMATURE' and o!=rig:bpy.data.objects.remove(o,do_unlink=True)
before=set(scene.objects)
bpy.ops.import_scene.fbx(filepath=str(ROOT/'assets/mixamo-running.fbx'))
added=[o for o in scene.objects if o not in before];source=next(o for o in added if o.type=='ARMATURE')
source.name='MixamoOriginal'
for o in added:o.hide_render=True
def src(suffix):return next(b for b in source.data.bones if b.name.endswith(suffix))
mapping={'Hips':'Hips','Spine1':'Spine','Chest':'Spine2','Head':'Head'}
for side in ('Left','Right'):
    for target,original_name in [('Clavicle','Shoulder'),('Arm','Arm'),('ForeArm','ForeArm'),('Hand','Hand'),('UpLeg','UpLeg'),('Leg','Leg'),('Foot','Foot')]:mapping[side+target]=side+original_name
forward=Vector((0,0,0))
for side in ('Left','Right'):forward+=source.matrix_world.to_3x3()@(src(side+'ToeBase').head_local-src(side+'Foot').head_local)
forward.z=0;forward.normalize()
alignment=forward.rotation_difference(Vector((0,-1,0))).to_matrix().to_4x4()
def normalized(m):
    result=m.to_quaternion().to_matrix().to_4x4();result.translation=m.translation;return result
source_rest={n:normalized(alignment@source.matrix_world@src(s).matrix_local) for n,s in mapping.items()}
start,end=[round(f) for f in source.animation_data.action.frame_range];count=end-start+1
samples=[];toe_samples=[]
for f in range(start,end+1):
    scene.frame_set(f)
    samples.append({n:normalized(alignment@source.matrix_world@source.pose.bones[src(s).name].matrix) for n,s in mapping.items()})
    toe_samples.append([tuple((alignment@source.matrix_world@source.pose.bones[src(s+'ToeBase').name].head)) for s in ('Left','Right')])
toe_samples=np.array(toe_samples)
step=(samples[-1]['Hips'].translation-samples[0]['Hips'].translation)*(count/(count-1));step.z=0
# Canonical source proxy only converts coordinate systems and bone names. Its
# independent global matrices are sampled directly from the untouched FBX.
proxy_data=bpy.data.armatures.new('MixamoCanonical');proxy=bpy.data.objects.new('MixamoCanonical',proxy_data);scene.collection.objects.link(proxy)
proxy_names={n:n.replace('UpLeg','Leg') if 'UpLeg' in n else n.replace('Leg','Shin') if n.endswith('Leg') else n for n in mapping}
bpy.context.view_layer.objects.active=proxy;bpy.ops.object.mode_set(mode='EDIT')
for n,s in mapping.items():
    b=proxy_data.edit_bones.new(proxy_names[n]);b.matrix=source_rest[n]
    b.length=(source.matrix_world.to_3x3()@(src(s).tail_local-src(s).head_local)).length
bpy.ops.object.mode_set(mode='OBJECT')
for i in range(90):
    scene.frame_set(i+1);lap,phase=divmod(i,count)
    for n in mapping:
        m=samples[phase][n].copy();m.translation+=step*lap
        b=proxy.pose.bones[proxy_names[n]];b.rotation_mode='QUATERNION';b.matrix=m
        b.keyframe_insert('location',frame=i+1);b.keyframe_insert('rotation_quaternion',frame=i+1)
proxy.hide_render=True;proxy.hide_set(True);source.hide_set(True)
rest={b.name:b.matrix_local.copy() for b in rig.data.bones}
parents={b.name:b.parent.name if b.parent else None for b in rig.data.bones}
rel={n:rest[p].inverted()@rest[n] if p else rest[n] for n,p in parents.items()}
reference={n:source_rest[n].to_3x3() for n in mapping}
for side in ('Left','Right'):
    n=side+'UpLeg';correction=reference[n].col[1].normalized().rotation_difference(rest[n].to_3x3().col[1].normalized()).to_matrix()
    for part in ('UpLeg','Leg'):reference[side+part]=correction@reference[side+part]
scale=sum(rig.data.bones['Left'+n].length for n in ('UpLeg','Leg'))/sum(proxy_data.bones[n].length for n in ('LeftLeg','LeftShin'))
for i in range(90):
    scene.frame_set(i+1);desired={}
    for n,p in parents.items():
        world=retarget_rotation(proxy.pose.bones[proxy_names[n]].matrix.to_3x3().normalized(),reference[n],rest[n].to_3x3())
        desired[n]=world
        q=(rel[n].to_3x3().inverted()@(desired[p].inverted()@world if p else world)).to_quaternion()
        b=rig.pose.bones[n];b.rotation_mode='QUATERNION';q.make_compatible(b.rotation_quaternion);b.rotation_quaternion=q;b.keyframe_insert('rotation_quaternion',frame=i+1)
    rig.location=(proxy.pose.bones['Hips'].head-samples[0]['Hips'].translation)*scale;rig.keyframe_insert('location',frame=i+1)
baseline=toe_samples[:,:,2].min(0)
velocity=np.linalg.norm(np.gradient(toe_samples[:,:,[0,1]],axis=0)*30,axis=-1)
contact=(toe_samples[:,:,2]<baseline[None,:]+.025)&(velocity<1.0)
contact[1:-1]|=contact[:-2]&contact[2:]
assert contact.sum(0).min()>0,contact.sum(0)
full=contact[np.arange(90)%count]
clearance=np.maximum(0,toe_samples[:,:,2]-baseline)[np.arange(90)%count]
meta=ROOT/'.cache/mixamo-contact.npz'
np.savez(meta,foot_contacts=np.repeat(full,3,axis=1).astype('float32'),foot_clearance=clearance.astype('float32'))
contact_report=plant_feet(scene,rig,hero,proxy,meta,allow_flight=True,swing_iterations=128)
camera=scene.camera;camera.animation_data_clear();camera.data.ortho_scale=1.4
for f in (1,90):
    scene.frame_set(f);center=Vector((rig.location.x,rig.location.y,.49));offset=Vector((2.7,0,.10))
    camera.location=center+offset;camera.rotation_euler=(-offset).to_track_quat('-Z','Y').to_euler();camera.keyframe_insert('location',frame=f);camera.keyframe_insert('rotation_euler',frame=f)
for layer in camera.animation_data.action.layers:
    for strip in layer.strips:
        for bag in strip.channelbags:
            for curve in bag.fcurves:
                for key in curve.keyframe_points:key.interpolation='LINEAR'
scene.frame_start=1;scene.frame_end=90;scene.render.fps=30;scene.frame_set(1)
for key in ('run_cycle_seconds','loop_displacement'):
    if key in rig:del rig[key]
bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'outputs/hero-mixamo-run.blend'),compress=True)
bpy.ops.object.select_all(action='DESELECT');hero.select_set(True);rig.select_set(True);bpy.context.view_layer.objects.active=rig
bpy.ops.export_scene.gltf(filepath=str(ROOT/'outputs/hero-mixamo-run.glb'),use_selection=True,export_animations=True,export_frame_range=True,export_force_sampling=True,export_animation_mode='SCENE')
report={'source':'assets/mixamo-running.fbx / Running With Intention','source_frames':count,'fps':30,'cycle_sample_seconds':count/30,
    'output_frames':90,'timing_scale':1,'leg_scale':scale,'bone_length_changes':False,'mesh_rest_position_error':float(np.abs(original-np.array([v.co[:] for v in hero.data.vertices])).max()),
    'body_rotation_edits':'No authored poses; source world-rotation deltas transferred; legs fitted to bind stance',
    'coordinate_forward_before':list(forward),'source_contacts_per_cycle':contact.sum(0).tolist(),'contact_correction':contact_report,
    'scope':'Candidate retarget; visual and export verification pending; raw source preserved'}
(ROOT/'docs/logs/hero-mixamo-run-rig.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report))

"""Retarget the downloaded Mixamo run; preserve its upper-body motion and timing."""
import bpy,json,math,sys,numpy as np
from pathlib import Path
from mathutils import Vector,Quaternion
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'scripts'))
from retarget import retarget_rotation
# Cache the previous result for an honest source / before / after comparison.
previous=[]
previous_path=ROOT/'outputs/hero-mixamo-run.blend'
if previous_path.exists():
    bpy.ops.wm.open_mainfile(filepath=str(previous_path))
    old=bpy.data.objects['TripoRunRig']
    for frame in range(1,91):
        bpy.context.scene.frame_set(frame)
        previous.append({b.name:[list(old.matrix_world@b.head),list(old.matrix_world@b.tail)] for b in old.pose.bones})
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
samples=[];toe_samples=[];source_floor=[]
for f in range(start,end+1):
    scene.frame_set(f)
    floor_points=[]
    for obj in added:
        if obj.type!='MESH':continue
        evaluated=obj.evaluated_get(bpy.context.evaluated_depsgraph_get());mesh=evaluated.to_mesh()
        floor_points.extend((alignment@evaluated.matrix_world@v.co).z for v in mesh.vertices);evaluated.to_mesh_clear()
    source_floor.append(min(floor_points))
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
# Match longitudinal directions, rather than reproducing the difference
# between a human bind stance and the character's spread-legged bind stance.
# This changes coordinate frames, not any sampled source motion.
reference={n:source_rest[n].to_3x3() for n in mapping}
axis_fit={n:rest[n].to_3x3().col[1].normalized().rotation_difference(reference[n].col[1].normalized()).to_matrix() for n in mapping}
scale=sum(rig.data.bones['Left'+n].length for n in ('UpLeg','Leg'))/sum(proxy_data.bones[n].length for n in ('LeftLeg','LeftShin'))
for i in range(90):
    scene.frame_set(i+1);desired={}
    for n,p in parents.items():
        world=retarget_rotation(proxy.pose.bones[proxy_names[n]].matrix.to_3x3().normalized(),reference[n],axis_fit[n]@rest[n].to_3x3())
        desired[n]=world
        q=(rel[n].to_3x3().inverted()@(desired[p].inverted()@world if p else world)).to_quaternion()
        b=rig.pose.bones[n];b.rotation_mode='QUATERNION';q.make_compatible(b.rotation_quaternion);b.rotation_quaternion=q;b.keyframe_insert('rotation_quaternion',frame=i+1)
    rig.location=(proxy.pose.bones['Hips'].head-samples[0]['Hips'].translation)*scale;rig.keyframe_insert('location',frame=i+1)
# Preserve every limb rotation. Only translate the whole character vertically
# to match the original mesh's scaled floor clearance. No leg IK, stride
# compression, knee pole, hand path or ankle clamp is used.
clearance=(np.array(source_floor)-min(source_floor))*scale
root_adjustments=[];after=[];source_lines=[]
lengths={b.name:b.length for b in rig.data.bones}
limbs=[side+part for side in ('Left','Right') for part in ('Clavicle','Arm','ForeArm','Hand','UpLeg','Leg','Foot')]
direction_error=[];bend_errors=[];old_bend_errors=[]
def angle(a,b):
    return math.degrees(a.normalized().angle(b.normalized()))
for i in range(90):
    scene.frame_set(i+1)
    evaluated=hero.evaluated_get(bpy.context.evaluated_depsgraph_get());mesh=evaluated.to_mesh()
    bottom=min((evaluated.matrix_world@v.co).z for v in mesh.vertices);evaluated.to_mesh_clear()
    adjustment=float(clearance[i%count]-bottom)
    rig.location.z+=adjustment;rig.keyframe_insert('location',frame=i+1);bpy.context.view_layer.update()
    root_adjustments.append(adjustment)
    after.append({b.name:[list(rig.matrix_world@b.head),list(rig.matrix_world@b.tail)] for b in rig.pose.bones})
    line={}
    for n in mapping:
        m=proxy.pose.bones[proxy_names[n]].matrix
        direction=m.to_3x3().col[1].normalized()
        line[n]=[list(m.translation),list(m.translation+direction*proxy_data.bones[proxy_names[n]].length)]
        if n in limbs:direction_error.append(angle(rig.pose.bones[n].tail-rig.pose.bones[n].head,direction))
    source_lines.append(line)
    for side in ('Left','Right'):
        for a,b in (('Arm','ForeArm'),('UpLeg','Leg')):
            n,k=side+a,side+b
            original_angle=angle(Vector(line[n][1])-Vector(line[n][0]),Vector(line[k][1])-Vector(line[k][0]))
            target_angle=angle(rig.pose.bones[n].tail-rig.pose.bones[n].head,rig.pose.bones[k].tail-rig.pose.bones[k].head)
            bend_errors.append(abs(original_angle-target_angle))
            if previous:
                old_angle=angle(Vector(previous[i][n][1])-Vector(previous[i][n][0]),Vector(previous[i][k][1])-Vector(previous[i][k][0]))
                old_bend_errors.append(abs(original_angle-old_angle))
assert max(direction_error)<.1, max(direction_error)
assert max(bend_errors)<.1, max(bend_errors)
assert all(abs(rig.data.bones[n].length-length)<1e-7 for n,length in lengths.items())
(ROOT/'docs/logs/hero-mixamo-run-skeleton.json').write_text(json.dumps({'source':source_lines,'previous':previous,'target':after}))
contact_report={'method':'Whole-body vertical translation matching scaled source mesh clearance; no leg IK or angle clamps',
    'limb_direction_error_max_degrees':max(direction_error),'elbow_knee_bend_error_max_degrees':max(bend_errors),
    'previous_elbow_knee_bend_error_max_degrees':max(old_bend_errors) if old_bend_errors else None,
    'root_vertical_correction_range_m':[min(root_adjustments),max(root_adjustments)],
    'foot_sliding':'Not corrected; retained for inspection instead of replacing source limb poses'}
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
    'body_rotation_edits':'Source limb world directions and elbow/knee bend preserved; target bind axes calibrated' ,
    'coordinate_forward_before':list(forward),'contact_correction':contact_report,
    'scope':'Direction/bend regression checks passed; visual and export checks separate'}
(ROOT/'docs/logs/hero-mixamo-run-rig.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report))

"""Coordinate clavicles, torso and arms without resizing the character."""
import math
import numpy as np
import bpy
from pathlib import Path
from mathutils import Vector, Quaternion


def coordinate_run(scene,rig,hero):
    assert 'LeftClavicle' not in rig.data.bones, 'Shoulders already added'
    samples=[]
    for f in range(1,92):
        scene.frame_set(f)
        samples.append({b.name:b.matrix.copy() for b in rig.pose.bones})
    hip_yaw=[]
    for poses in samples[:90]:
        delta=poses['Hips'].to_3x3() @ rig.data.bones['Hips'].matrix_local.to_3x3().inverted()
        front=delta @ Vector((0,-1,0));hip_yaw.append(math.atan2(front.x,-front.y))
    center=float(np.mean(hip_yaw));extent=max(abs(v-center) for v in hip_yaw)
    bpy.context.view_layer.objects.active=rig
    bpy.ops.object.mode_set(mode='EDIT')
    for side,sign in (('Left',1),('Right',-1)):
        arm=rig.data.edit_bones[side+'Arm']
        bone=rig.data.edit_bones.new(side+'Clavicle')
        bone.head=(sign*.035,.012,.535);bone.tail=arm.head.copy()
        bone.parent=rig.data.edit_bones['Chest'];arm.parent=bone
    bpy.ops.object.mode_set(mode='OBJECT')
    for b in rig.pose.bones:b.rotation_mode='QUATERNION'
    for side in ('Left','Right'):hero.vertex_groups.new(name=side+'Clavicle')
    def smooth(x,a,b):
        t=np.clip((x-a)/(b-a),0,1);return float(t*t*(3-2*t))
    transferred=0
    torso={hero.vertex_groups[n].index for n in ('Hips','Spine1','Chest')}
    # A continuous shoulder field carries the coat into the clavicle, while
    # keeping the hood, scarf, gloves and lower body on their existing groups.
    for v in hero.data.vertices:
        x,y,z=v.co
        mix=.65*smooth(abs(x),.075,.17)*smooth(z,.425,.48)*(1-smooth(z,.535,.565))
        if mix<1e-8:continue
        weights=[(g.group,g.weight) for g in v.groups if g.group in torso]
        amount=sum(w for _,w in weights)*mix
        for idx,w in weights:hero.vertex_groups[idx].add([v.index],w*(1-mix),'REPLACE')
        if amount>1e-8:
            hero.vertex_groups[('Left' if x>0 else 'Right')+'Clavicle'].add([v.index],amount,'REPLACE');transferred+=1
    shoulder_spread=[];lean=[]
    # Preserve every existing rest matrix. New shoulder bones change parent
    # spaces, so bake desired world orientations back into the new hierarchy.
    ordered=list(rig.pose.bones)
    for f,old in enumerate(samples,1):
        scene.frame_set(f)
        phase=(hip_yaw[(f-1)%90]-center)/extent
        chest=rig.data.bones['Chest'];old_delta=old['Chest'].to_3x3() @ chest.matrix_local.to_3x3().inverted()
        e=old_delta.to_euler('XYZ')
        e.x-=math.radians(7)
        e.z=math.radians(3)-math.radians(8)*phase
        chest_world=e.to_matrix() @ chest.matrix_local.to_3x3()
        change=chest_world @ old['Chest'].to_3x3().inverted()
        desired={name:m.to_3x3() for name,m in old.items()}
        desired['Chest']=chest_world
        desired['Head']=change @ old['Head'].to_3x3()
        for side in ('Left','Right'):
            cb=rig.data.bones[side+'Clavicle']
            desired[cb.name]=Quaternion(Vector((0,0,1)),math.radians(-6)*phase).to_matrix() @ chest_world @ chest.matrix_local.to_3x3().inverted() @ cb.matrix_local.to_3x3()
            for part in ('Arm','ForeArm','Hand'):desired[side+part]=change @ old[side+part].to_3x3()
        for b in ordered:
            parent=desired[b.parent.name] if b.parent else None
            bind=b.parent.bone.matrix_local.to_3x3().inverted() @ b.bone.matrix_local.to_3x3() if b.parent else b.bone.matrix_local.to_3x3()
            q=(bind.inverted() @ parent.inverted() @ desired[b.name] if parent is not None else bind.inverted() @ desired[b.name]).to_quaternion()
            q.make_compatible(b.rotation_quaternion);b.rotation_quaternion=q;b.keyframe_insert('rotation_quaternion',frame=f)
        scene.view_layers[0].update()
        shoulder_spread.append(rig.pose.bones['LeftArm'].head.y-rig.pose.bones['RightArm'].head.y)
        up=e.to_matrix() @ Vector((0,0,1));lean.append(math.degrees(math.atan2(-up.y,up.z)))
    rig['coordinated_shoulders']=True
    timing=settle_cadence(scene,rig,hero)
    scene.frame_set(1)
    return {'bones':len(rig.data.bones),'clavicle_weighted_vertices':transferred,'timing':timing,
            'shoulder_front_back_difference_range_m':[min(shoulder_spread),max(shoulder_spread)],
            'chest_forward_lean_range_degrees':[min(lean),max(lean)],
            'method':'Chest counter-rotates against pelvis; independent clavicle rotation; continuous shoulder coat weights; original rest geometry retained; lower poses phase-averaged for cadence.'}


def settle_cadence(scene,rig,hero):
    """Average equivalent cycles, then bake five 0.6s cycles in three seconds."""
    travel=Vector(rig['loop_displacement']);rate=5/6
    motion=np.load(Path(__file__).resolve().parents[1]/'outputs/run.npz')
    contacts=np.stack((motion['foot_contacts'][:,:3].max(1)>.5,motion['foot_contacts'][:,3:].max(1)>.5),axis=1)
    sole_ids=[v.index for v in hero.data.vertices if v.co.z<.045]
    frames=[]
    for i in range(30):
        scene.frame_set(i+1)
        obj=hero.evaluated_get(scene.view_layers[0].depsgraph);mesh=obj.to_mesh()
        soles=np.array([(obj.matrix_world @ mesh.vertices[j].co)[:] for j in sole_ids])-np.array(travel)*(i/90)
        obj.to_mesh_clear()
        frames.append((rig.location.copy()-travel*(i/90),{b.name:b.rotation_quaternion.copy() for b in rig.pose.bones},soles,
                       {side:rig.pose.bones[side+'Foot'].matrix.to_quaternion() for side in ('Left','Right')}))
    cycle=[]
    for i in range(15):
        a,b=frames[i],frames[i+15]
        cycle.append((a[0].lerp(b[0],.5),{n:q.slerp(b[1][n],.5) for n,q in a[1].items()},(a[2]+b[2])*.5,
                      {side:a[3][side].slerp(b[3][side],.5) for side in ('Left','Right')}))
    lift_max=0;contact_max=0;ankle_correction=0
    for i in range(91):
        phase=i*rate%15;a=int(phase);b=(a+1)%15;t=phase-a
        scene.frame_set(i+1)
        rig.location=cycle[a][0].lerp(cycle[b][0],t)+travel*(i*rate/90)
        for bone in rig.pose.bones:bone.rotation_quaternion=cycle[a][1][bone.name].slerp(cycle[b][1][bone.name],t)
        scene.view_layers[0].update()
        source_phase=i*1.25%22.5;other=source_phase+22.5
        stance=contacts[int(math.floor(source_phase))] | contacts[int(math.ceil(source_phase))%45] | contacts[int(math.floor(other))] | contacts[int(math.ceil(other))%45]
        for j,side in enumerate(('Left','Right')):
            foot=rig.pose.bones[side+'Foot']
            world=cycle[a][3][side].slerp(cycle[b][3][side],t).to_matrix()
            bind=foot.parent.bone.matrix_local.to_3x3().inverted() @ foot.bone.matrix_local.to_3x3()
            q=(bind.inverted() @ foot.parent.matrix.to_3x3().inverted() @ world).to_quaternion()
            q.make_compatible(foot.rotation_quaternion);foot.rotation_quaternion=q
            q=q.normalized()
            angle=2*math.acos(min(1,abs(q.w)))
            if not stance[j] and angle>math.radians(40):
                foot.rotation_quaternion=q.slerp(Quaternion((1,0,0,0)) if q.w>=0 else Quaternion((-1,0,0,0)),1-math.radians(40)/angle)
                ankle_correction=max(ankle_correction,math.degrees(angle)-40)
        scene.view_layers[0].update()
        obj=hero.evaluated_get(scene.view_layers[0].depsgraph);mesh=obj.to_mesh()
        expected=cycle[a][2]*(1-t)+cycle[b][2]*t+np.array(travel)*(i*rate/90)
        actual=np.array([(obj.matrix_world @ mesh.vertices[j].co)[:] for j in sole_ids])
        planted=expected[:,2]<.0002
        correction=np.mean(expected[planted,:2]-actual[planted,:2],axis=0) if planted.any() else np.zeros(2)
        bottom=min((obj.matrix_world @ v.co).z for v in mesh.vertices);obj.to_mesh_clear()
        rig.location.x+=float(correction[0]);rig.location.y+=float(correction[1])
        lift=max(0,max(0,float(expected[:,2].min()))-bottom);rig.location.z+=lift
        lift_max=max(lift_max,lift);contact_max=max(contact_max,float(np.linalg.norm(correction)))
        rig.keyframe_insert('location',frame=i+1)
        for bone in rig.pose.bones:bone.keyframe_insert('rotation_quaternion',frame=i+1)
    rig['loop_displacement']=list(travel*rate)
    rig['run_timing_rate']=1.25;rig['run_cycle_seconds']=.6
    rig['canonical_run_cycle']=True
    return {'cycle_seconds':.6,'cycles_in_3_seconds':5,'steps_per_minute':200,
            'mean_speed_m_s':float(travel.length*rate/3),'max_ground_clearance_lift_m':lift_max,
            'max_contact_translation_correction_m':contact_max,
            'max_air_ankle_limit_correction_degrees':ankle_correction,
            'method':'Average the two equivalent 15-frame source cycles; periodic quaternion slerp to 18 frames; preserve contact trajectory and swing clearance.'}

"""Contact-aware, fixed-length two-bone leg solve for the hero's large boots."""
import math
import bpy
import numpy as np
from mathutils import Vector, Euler
from hero_preview import boot_rotation
from retarget import retarget_rotation

def plant_feet(scene,rig,hero,source,motion_path,allow_flight=False):
    motion=np.load(motion_path,allow_pickle=False)
    cyclic='loop_displacement' in motion
    contacts=np.stack([motion['foot_contacts'][:,:3].max(1)>.5,
                       motion['foot_contacts'][:,3:].max(1)>.5],axis=1)
    scale=sum(rig.data.bones['Left'+n].length for n in ('UpLeg','Leg'))/sum(source.data.bones[n].length for n in ('LeftLeg','LeftShin'))
    sides=('Left','Right');roots=[];poses=[];ankles=[];source_hips=[];source_rot=[];source_leg_z=[]
    for f in range(1,91):
        scene.frame_set(f)
        roots.append(rig.location.copy())
        poses.append({n:b.matrix.copy() for n,b in rig.pose.bones.items()})
        ankles.append([source.pose.bones[s+'Foot'].head[: ] for s in sides])
        source_hips.append(source.pose.bones['Hips'].head[:])
        source_leg_z.append([source.pose.bones[s+'Leg'].head.z*scale for s in sides])
        source_rot.append([source.pose.bones[s+'Foot'].matrix.to_quaternion().to_matrix() for s in sides])
    ankles=np.array(ankles)*scale;source_hips=np.array(source_hips)*scale
    # Walk contact gaps at the clip boundary use the lower source ankle.
    for f in range(90):
        if not allow_flight and not contacts[f].any():
            contacts[f,np.argmin(ankles[f,:,2])]=True
    rest_coords=np.array([v.co[:] for v in hero.data.vertices])
    # Rigid soles prevent the calf's rotation from stretching the boot bottom.
    rigid_counts=[]
    for side,sign in zip(sides,(1,-1)):
        ids=np.flatnonzero((rest_coords[:,0]*sign>0)&(rest_coords[:,2]<.075)).tolist()
        for group in hero.vertex_groups:
            group.remove(ids)
        hero.vertex_groups[side+'Foot'].add(ids,1.0,'REPLACE')
        rigid_counts.append(len(ids))
    targets=ankles.copy();orientations=[[],[]];vertical_offsets=[]
    for j,side in enumerate(sides):
        rest=rig.data.bones[side+'Foot'].matrix_local
        bind_source=source.data.bones[side+'Foot']
        targets[:,j,0]+=rest.translation.x-bind_source.head_local.x*scale
        targets[:,j,1]+=rig.data.bones['Hips'].head_local.y-source_hips[0,1]
        original_xy=targets[:,j,:2].copy()
        assert contacts[:,j].any(),f'{side} foot never contacts ground'
        baseline=np.median(ankles[contacts[:,j],j,2])
        vertical_offsets.append(rest.translation.z-baseline)
        targets[:,j,2]=rest.translation.z+np.maximum(0,ankles[:,j,2]-baseline)
        yaw=[]
        for f in range(90):
            world=retarget_rotation(source_rot[f][j],bind_source.matrix_local.to_3x3(),rest.to_3x3())
            yaw.append((world@rest.to_3x3().inverted()).to_euler('XYZ').z)
            orientations[j].append(boot_rotation(world,rest.to_3x3(),35 if allow_flight else 20))
        # Plant each contact interval at one anchor. Blend its small trajectory
        # correction into swing over three frames, avoiding a snap at touchdown.
        start=0
        while start<90:
            if not contacts[start,j]:
                start+=1;continue
            end=start
            while end+1<90 and contacts[end+1,j]:end+=1
            anchor=targets[start:end+1,j,:2].mean(0)
            angle=float(np.mean(np.unwrap(yaw[start:end+1])))
            for f in range(start,end+1):
                targets[f,j,:2]=anchor;targets[f,j,2]=rest.translation.z
                orientations[j][f]=Euler((0,0,angle)).to_matrix()@rest.to_3x3()
            for edge,direction in ((start,-1),(end,1)):
                for step in range(1,4):
                    f=edge+direction*step
                    if 0<=f<90 and not contacts[f,j]:
                        weight=(4-step)/4
                        targets[f,j,:2]+=weight*(anchor-original_xy[edge])
                        swing=orientations[j][f].to_quaternion()
                        stance=orientations[j][edge].to_quaternion()
                        orientations[j][f]=swing.slerp(stance,weight).to_matrix()
            start=end+1
        sole=rest_coords[(rest_coords[:,0]*(1 if j==0 else -1)>0)&(rest_coords[:,2]<.075)]-np.array(rest.translation)
        for f in range(90):
            rotation=orientations[j][f]@rest.to_3x3().inverted()
            lowest=float((sole @ np.array(rotation)[2]).min())
            clearance=0 if contacts[f,j] else .003
            if not contacts[f,j] and 'foot_clearance' in motion:
                clearance=max(clearance,float(motion['foot_clearance'][f,j])*scale)
            targets[f,j,2]=max(targets[f,j,2],-lowest+clearance)
    raw_z=[]
    for f in range(90):
        ceilings=[]
        for j,side in enumerate(sides):
            hip=poses[f][side+'UpLeg'].translation+Vector((roots[f].x,roots[f].y,0))
            horiz=Vector(targets[f,j])-hip;horiz.z=0
            length=sum(rig.data.bones[side+n].length for n in ('UpLeg','Leg'))*.985
            assert horiz.length<length,'Requested foot target is outside leg reach'
            ceilings.append(targets[f,j,2]+math.sqrt(length*length-horiz.length_squared)-hip.z)
        natural=-.02+source_hips[f,2]-source_hips[0,2]
        if allow_flight:
            natural=float(np.mean([source_leg_z[f][j]+vertical_offsets[j]-poses[f][s+'UpLeg'].translation.z for j,s in enumerate(sides)]))-.003
        values=np.array([natural,*ceilings])
        raw_z.append(float(values.min()-.004*np.log(np.exp(-(values-values.min())/.004).sum())))
    smooth_z=np.convolve(np.pad(raw_z,(3,3),mode='wrap' if cyclic else 'edge'),np.array([1,6,15,20,15,6,1])/64,mode='valid')
    # A constant downward adjustment keeps every target reachable after
    # smoothing, instead of reintroducing a hard per-frame reach clamp.
    smoothing_drop=max(0,float(np.max(smooth_z-np.array(raw_z))))
    smooth_z-=smoothing_drop
    root_z=[];max_reach_error=0;max_upper_error=0
    for f in range(1,91):
        scene.frame_set(f)
        upper={n:b.rotation_quaternion.copy() for n,b in rig.pose.bones.items() if not any(n==s+part for s in sides for part in ('UpLeg','Leg','Foot'))}
        z=float(smooth_z[f-1])
        rig.location=Vector((roots[f-1].x,roots[f-1].y,z));rig.keyframe_insert('location',frame=f)
        bpy.context.view_layer.update()
        for j,side in enumerate(sides):
            thigh,shin,foot=[rig.pose.bones[side+n] for n in ('UpLeg','Leg','Foot')]
            hip=thigh.head.copy();ankle=Vector(targets[f-1,j])-rig.location
            direction=ankle-hip;distance=direction.length;direction.normalize()
            l1,l2=thigh.bone.length,shin.bone.length
            a=(l1*l1-l2*l2+distance*distance)/(2*distance)
            pole=Vector((0,-1,0));perp=(pole-direction*pole.dot(direction)).normalized()
            knee=hip+direction*a+perp*math.sqrt(max(0,l1*l1-a*a))
            desired={}
            for pb,vector in ((thigh,knee-hip),(shin,ankle-knee)):
                previous=poses[f-1][pb.name].to_quaternion().to_matrix()
                desired[pb.name]=previous.col[1].rotation_difference(vector.normalized()).to_matrix()@previous
            desired[foot.name]=orientations[j][f-1]
            for pb in (thigh,shin,foot):
                parent=desired.get(pb.parent.name,pb.parent.matrix.to_quaternion().to_matrix())
                bind=pb.parent.bone.matrix_local.to_3x3().inverted()@pb.bone.matrix_local.to_3x3()
                q=(bind.inverted()@parent.inverted()@desired[pb.name]).to_quaternion()
                q.make_compatible(pb.rotation_quaternion);pb.rotation_quaternion=q
                pb.keyframe_insert('rotation_quaternion',frame=f)
                bpy.context.view_layer.update()
            max_reach_error=max(max_reach_error,(rig.matrix_world @ foot.head-Vector(targets[f-1,j])).length)
        for n,q in upper.items():
            max_upper_error=max(max_upper_error,float(np.abs(np.array(q)-np.array(rig.pose.bones[n].rotation_quaternion)).max()))
        root_z.append(z)
    assert max_reach_error<1e-5,max_reach_error
    assert max_upper_error<1e-6,max_upper_error
    if cyclic:
        displacement=motion['loop_displacement']*scale
        travel=Vector((float(displacement[0]),float(-displacement[2]),0))
        rig['loop_displacement']=list(travel)
        scene.frame_set(1)
        endpoint={n:b.rotation_quaternion.copy() for n,b in rig.pose.bones.items()}
        first_location=rig.location.copy()
        scene.frame_set(91)
        rig.location=first_location+travel;rig.keyframe_insert('location',frame=91)
        for n,q in endpoint.items():
            rig.pose.bones[n].rotation_quaternion=q
            rig.pose.bones[n].keyframe_insert('rotation_quaternion',frame=91)
        scene.frame_set(1)
    return {'max_ankle_target_error_m':max_reach_error,'upper_body_rotation_error':max_upper_error,
            'root_vertical_frame_acceleration_max_m':float(np.abs(np.diff(root_z,n=2)).max()),
            'smoothing_downward_adjustment_m':smoothing_drop,
            'rigid_sole_vertices':rigid_counts,'stance_frames':contacts.sum(0).tolist(),
            'source_flight_frames_preserved':int((~contacts.any(1)).sum()),
            'method':'Fixed-length two-bone leg solve, source contact anchors, rigid soles and swing boot clearance'}

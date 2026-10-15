"""Character-specific upper-body posing for a readable side-view run."""
import math
import numpy as np
from mathutils import Vector,Matrix


def joint_frame(vector,normal):
    y=vector.normalized()
    x=normal-y*normal.dot(y)
    x.normalize();z=x.cross(y).normalized();x=y.cross(z).normalized()
    return Matrix((x,y,z)).transposed()


def pose_run_arms(scene,rig):
    """Keep generated timing with compact, low, rear-biased game-run arms."""
    samples=[]
    for f in range(1,91):
        scene.frame_set(f)
        samples.append({s:(rig.pose.bones[s+'Hand'].head-rig.pose.bones['Chest'].head).copy() for s in ('Left','Right')})
    means={s:np.mean([p[s][:] for p in samples],axis=0) for s in ('Left','Right')}
    for side in ('Left','Right'):
        p=np.array([value[side][:] for value in samples])
        smooth=sum(weight*np.roll(p,offset,axis=0) for offset,weight in zip(range(-2,3),(1,4,6,4,1)))/16
        for f in range(90):samples[f][side]=Vector(smooth[f])
    error=0;wrist_max=0
    for f in range(1,91):
        scene.frame_set(f)
        chest=rig.pose.bones['Chest']
        for side,sign in (('Left',1),('Right',-1)):
            arm,fore,hand=[rig.pose.bones[side+n] for n in ('Arm','ForeArm','Hand')]
            p=samples[f-1][side];mean=means[side]
            gain=1.0 if side=='Right' else .88
            height=-.063 if side=='Right' else -.070
            target=chest.head+Vector((sign*.18+(p.x-mean[0])*.12,
                                    .025+(p.y-mean[1])*gain,
                                    height+(p.z-mean[2])*.45))
            shoulder=arm.head.copy();direction=target-shoulder
            l1,l2=arm.bone.length,fore.bone.length
            distance=min(direction.length,(l1+l2)*.94)
            direction.normalize();target=shoulder+direction*distance
            a=(l1*l1-l2*l2+distance*distance)/(2*distance)
            pole=Vector((sign*.15,1,-.25));perp=(pole-direction*pole.dot(direction)).normalized()
            elbow=shoulder+direction*a+perp*math.sqrt(max(0,l1*l1-a*a))
            # A shared hinge plane avoids the 180-degree roll singularity of
            # projecting a fixed reference axis onto each moving forearm.
            normal=(elbow-shoulder).cross(target-elbow).normalized()
            rest_upper=arm.bone.tail_local-arm.bone.head_local
            rest_fore=fore.bone.tail_local-fore.bone.head_local
            rest_normal=rest_upper.cross(rest_fore).normalized()
            desired={}
            for pb,vector in ((arm,elbow-shoulder),(fore,target-elbow)):
                rest_frame=joint_frame(pb.bone.tail_local-pb.bone.head_local,rest_normal)
                desired[pb.name]=joint_frame(vector,normal) @ rest_frame.inverted() @ pb.bone.matrix_local.to_3x3()
            desired[hand.name]=desired[fore.name] @ fore.bone.matrix_local.to_3x3().inverted() @ hand.bone.matrix_local.to_3x3()
            for pb in (arm,fore,hand):
                parent=desired.get(pb.parent.name,pb.parent.matrix.to_3x3())
                bind=pb.parent.bone.matrix_local.to_3x3().inverted() @ pb.bone.matrix_local.to_3x3()
                q=(bind.inverted() @ parent.inverted() @ desired[pb.name]).to_quaternion()
                q.make_compatible(pb.rotation_quaternion);pb.rotation_quaternion=q;pb.keyframe_insert('rotation_quaternion',frame=f)
                scene.view_layers[0].update()
            error=max(error,(hand.head-target).length)
            wrist_max=max(wrist_max,math.degrees(2*math.acos(min(1,abs(hand.rotation_quaternion.normalized().w)))))
    assert error<1e-5,error
    return {'max_wrist_target_error_m':error,'max_wrist_rotation_degrees':wrist_max,
            'method':'Generated timing; compact low rear-biased paths with small side asymmetry; fixed-length arm IK; neutral wrist'}

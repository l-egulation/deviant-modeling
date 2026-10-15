"""Speed up the approved run without changing its fitted skeleton or poses."""
import math
import numpy as np
from mathutils import Vector


def accelerate_run(scene, rig, hero):
    assert 'run_timing_rate' not in rig, 'Run already retimed'
    rate=1.5
    travel=Vector(rig['loop_displacement'])
    rest=np.array([v.co[:] for v in hero.data.vertices])
    sole_ids=np.flatnonzero(rest[:,2]<.045)
    samples=[]
    soles=[]
    # The accepted 90-frame clip repeats its two-cycle 45-frame block.
    for f in range(1,46):
        scene.frame_set(f)
        samples.append((rig.location.copy()-travel*((f-1)/90),
                        {b.name:b.rotation_quaternion.copy() for b in rig.pose.bones}))
        obj=hero.evaluated_get(scene.view_layers[0].depsgraph);mesh=obj.to_mesh()
        soles.append(np.array([(obj.matrix_world @ mesh.vertices[int(j)].co)[:] for j in sole_ids])-np.array(travel)*((f-1)/90))
        obj.to_mesh_clear()
    records=[]
    for i in range(91):
        phase=(i*rate)%45
        a=int(math.floor(phase));t=phase-a;b=(a+1)%45
        root=samples[a][0].lerp(samples[b][0],t)+travel*(i*rate/90)
        rotations={n:q.slerp(samples[b][1][n],t) for n,q in samples[a][1].items()}
        records.append((root,rotations))
    lifts=[];contact_corrections=[]
    for f,(root,rotations) in enumerate(records,1):
        scene.frame_set(f);rig.location=root
        for name,q in rotations.items():
            rig.pose.bones[name].rotation_quaternion=q
        scene.view_layers[0].update()
        obj=hero.evaluated_get(scene.view_layers[0].depsgraph);mesh=obj.to_mesh()
        phase=((f-1)*rate)%45;a=int(phase);t=phase-a;b=(a+1)%45
        expected=soles[a]*(1-t)+soles[b]*t+np.array(travel)*((f-1)*rate/90)
        actual=np.array([(obj.matrix_world @ mesh.vertices[int(j)].co)[:] for j in sole_ids])
        planted=expected[:,2]<.0002
        correction=np.mean(expected[planted,:2]-actual[planted,:2],axis=0) if planted.any() else np.zeros(2)
        bottom=min((obj.matrix_world @ v.co).z for v in mesh.vertices)
        obj.to_mesh_clear()
        rig.location.x+=float(correction[0]);rig.location.y+=float(correction[1])
        contact_corrections.append(float(np.linalg.norm(correction)))
        # Preserve source swing clearance as well as avoiding penetration.
        # Lifting only to zero can create a false grounded sample at toe-off.
        lift=max(0,max(0,float(expected[:,2].min()))-bottom)
        rig.location.z+=lift;lifts.append(lift)
        rig.keyframe_insert('location',frame=f)
        for bone in rig.pose.bones:bone.keyframe_insert('rotation_quaternion',frame=f)
    rig['loop_displacement']=list(travel*rate)
    rig['run_timing_rate']=rate
    rig['run_cycle_seconds']=.5
    scene.frame_set(1)
    return {'rate':rate,'cycle_seconds':.5,'cycles_in_3_seconds':6,
            'mean_speed_m_s':float(travel.length*rate/3),
            'maximum_interpolated_ground_lift_m':max(lifts),
            'maximum_contact_translation_correction_m':max(contact_corrections),
            'method':'Periodic quaternion slerp, root travel retimed together; unchanged rest geometry and joint poses at original samples.'}

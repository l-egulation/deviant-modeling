"""Inspect all rendered poses for foot sliding, framing and residual motion issues."""
import os
import bpy,json,numpy as np
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
MOTION = os.environ.get('HERO_MOTION', 'walk')
assert MOTION in ('walk', 'run')
LOG_STEM = 'hero' if MOTION == 'walk' else 'hero-run'
bpy.ops.wm.open_mainfile(filepath=str(ROOT/f'outputs/hero-{MOTION}.blend'))
scene=bpy.context.scene;rig=bpy.data.objects['HeroRig'];hero=bpy.data.objects['InkHero'];camera=scene.camera
rest=np.array([v.co[:] for v in hero.data.vertices]);sole=np.flatnonzero(rest[:,2]<.045)
last=None;speeds=[];near_ground_speeds=[];bottoms=[];roots=[];quats=[];frames_min=[];frames_max=[]
length_error=0
for f in range(1,91):
    scene.frame_set(f);deps=bpy.context.evaluated_depsgraph_get();obj=hero.evaluated_get(deps);mesh=obj.to_mesh()
    coords=np.empty(len(mesh.vertices)*3);mesh.vertices.foreach_get('co',coords);coords=coords.reshape(-1,3)
    world=coords @ np.array(obj.matrix_world.to_3x3()).T+np.array(obj.matrix_world.translation)
    assert np.isfinite(world).all()
    points=world[sole]
    if last is not None:
        velocity=np.linalg.norm((points-last)[:,:2],axis=1)*30
        near=(points[:,2]<.003)&(last[:,2]<.003)
        near_ground_speeds.extend(velocity[near])
        # A rolling rigid sole moves points above the contact plane. Measure
        # sliding at actual ground contact, and retain the old 3mm band as data.
        tolerance=.0002 if MOTION == 'run' else .003
        contact=(points[:,2]<tolerance)&(last[:,2]<tolerance)
        speeds.extend(velocity[contact])
    last=points.copy();bottoms.append(float(world[:,2].min()));roots.append(rig.location[:])
    projection=np.array(camera.calc_matrix_camera(deps,x=512,y=512)@camera.matrix_world.inverted())
    clip=np.column_stack((world,np.ones(len(world))))@projection.T
    uv=(clip[:,:2]/clip[:,3:4]+1)/2
    frames_min.append(uv.min(0));frames_max.append(uv.max(0));obj.to_mesh_clear()
    quats.append([b.rotation_quaternion.normalized()[:] for b in rig.pose.bones])
    for b in rig.pose.bones:
        assert max(abs(s-1) for s in b.scale)<1e-6
        length_error=max(length_error,abs(b.length-b.bone.length))
quats=np.array(quats);roots=np.array(roots)
seam=float(np.mean(2*np.arccos(np.clip(np.abs(np.sum(quats[0]*quats[-1],axis=1)),-1,1)))*180/np.pi)
lo=np.min(frames_min,axis=0);hi=np.max(frames_max,axis=0)
assert min(bottoms)>-1e-5
if MOTION == 'walk':
    assert max(bottoms)<.003
assert len(speeds)>20 and np.mean(speeds)<.005,(len(speeds),float(np.mean(speeds)))
assert np.mean(near_ground_speeds)<.005,float(np.mean(near_ground_speeds))
assert lo.min()>.03 and hi.max()<.97
assert length_error<1e-5
report={'status':'PASS_WITH_KNOWN_LIMITATION','frames_checked':90,'fixed_sole_contact_mean_speed_m_s':float(np.mean(speeds)),'fixed_sole_contact_speed_p95_m_s':float(np.percentile(speeds,95)),'sole_contact_vertex_pairs':len(speeds),'min_ground_height_m':min(bottoms),'max_ground_height_m':max(bottoms),'frame_bounds_min_uv':lo.tolist(),'frame_bounds_max_uv':hi.tolist(),'max_bone_length_error_m':length_error,'root_vertical_second_difference_max_m_per_frame2':float(np.abs(np.diff(roots[:,2],n=2)).max()),'start_end_mean_pose_difference_degrees':seam,'seamless_loop':False,'known_limitation':'Original three-second clip is not a seamless game loop; wrap-around changes the pose. No claim of final cloth topology or collision quality.'}
report.update(contact_plane_tolerance_m=.0002 if MOTION == 'run' else .003,
              near_ground_3mm_mean_speed_m_s=float(np.mean(near_ground_speeds)))
if 'loop_displacement' in rig:
    scene.frame_set(91)
    endpoint=np.array([b.rotation_quaternion.normalized()[:] for b in rig.pose.bones])
    error=float(np.abs(endpoint-quats[0]).max())
    assert error<1e-6
    allq=np.concatenate((quats,endpoint[None]),axis=0)
    steps=np.mean(2*np.arccos(np.clip(np.abs(np.sum(allq[:-1]*allq[1:],axis=2)),-1,1)),axis=1)*180/np.pi
    assert steps[-1]<np.percentile(steps[:-1],95)*1.5+3
    report.update(status='PASS',seamless_loop=True,loop_endpoint_rotation_error=error,
                  wrap_step_mean_angle_degrees=float(steps[-1]),normal_step_angle_p95_degrees=float(np.percentile(steps[:-1],95)),
                  known_limitation='Loop and contact tests pass; final cloth collision and artistic style remain visual checks.')
(ROOT/f'docs/logs/{LOG_STEM}-review-after.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))

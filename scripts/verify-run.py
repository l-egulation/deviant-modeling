"""Check unchanged character proportions, run flight, loop endpoint and skin rigidity."""
import bpy,json,numpy as np
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(ROOT/'outputs/hero-walk.blend'))
walk_rest={b.name:np.array(b.matrix_local) for b in bpy.data.objects['HeroRig'].data.bones}
walk_vertices=np.array([v.co[:] for v in bpy.data.objects['InkHero'].data.vertices])
bpy.ops.wm.open_mainfile(filepath=str(ROOT/'outputs/hero-run.blend'))
scene=bpy.context.scene;rig=bpy.data.objects['HeroRig'];hero=bpy.data.objects['InkHero'];camera=scene.camera
rest=np.array([v.co[:] for v in hero.data.vertices])
rest_error=float(np.abs(rest-walk_vertices).max())
bone_error=max(float(np.abs(np.array(b.matrix_local)-walk_rest[b.name]).max()) for b in rig.data.bones)
assert rest_error<1e-7 and bone_error<1e-7
flight=[];poses=[];roots=[];cameras=[];skin_error=0;neck_error=0
for f in range(1,92):
    scene.frame_set(f)
    poses.append(np.array([b.rotation_quaternion.normalized()[:] for b in rig.pose.bones]))
    roots.append(rig.location[:]);cameras.append(camera.matrix_world.translation[:])
    obj=hero.evaluated_get(bpy.context.evaluated_depsgraph_get());mesh=obj.to_mesh()
    v=np.empty(len(mesh.vertices)*3);mesh.vertices.foreach_get('co',v);v=v.reshape(-1,3)
    world=v @ np.array(obj.matrix_world.to_3x3()).T+np.array(obj.matrix_world.translation)
    flight.append(float(world[:,2].min())>.002)
    for side,sign in [('Left',1),('Right',-1)]:
        ids=np.flatnonzero((rest[:,0]*sign>.215)&(rest[:,2]>.255)&(rest[:,2]<.365))
        bone=rig.pose.bones[side+'Hand']
        transform=rig.matrix_world @ bone.matrix @ bone.bone.matrix_local.inverted()
        expected=rest[ids]@np.array(transform.to_3x3()).T+np.array(transform.translation)
        skin_error=max(skin_error,float(np.abs(world[ids]-expected).max()))
    chest=rig.pose.bones['Chest'];head=rig.pose.bones['Head']
    a=chest.matrix @ chest.bone.matrix_local.inverted();b=head.matrix @ head.bone.matrix_local.inverted()
    neck_error=max(neck_error,float(np.abs(np.array(a)-np.array(b)).max()))
    obj.to_mesh_clear()
poses=np.array(poses);roots=np.array(roots);cameras=np.array(cameras)
seam=float(np.abs(poses[0]-poses[-1]).max())
travel=np.array(rig['loop_displacement'])
root_seam=float(np.abs(roots[-1]-roots[0]-travel).max())
camera_residual=float(np.abs(cameras-np.linspace(cameras[0],cameras[-1],91)).max())
assert seam<1e-6 and root_seam<1e-6 and camera_residual<1e-6
assert skin_error<1e-5 and neck_error<1e-5
assert 5<sum(flight[:90])<70
report={'status':'PASS','mesh_rest_position_difference_from_walk_m':rest_error,'bone_rest_matrix_difference_from_walk':bone_error,'bones':len(walk_rest),'flight_frames':sum(flight[:90]),'loop_rotation_endpoint_error':seam,'loop_root_endpoint_error_m':root_seam,'camera_constant_velocity_error_m':camera_residual,'glove_rigid_skin_error_m':skin_error,'hood_scarf_deformation_transform_error':neck_error,'clip_displacement_m':travel.tolist(),'mean_speed_m_s':float(np.linalg.norm(travel[:2])/3),'scope':'Same character proportions; running air phase retained; loop endpoint matches after travel normalization. Cloth collision and subjective style remain visual checks.'}
(ROOT/'docs/logs/hero-run-validation.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))

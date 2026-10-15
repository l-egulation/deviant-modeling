"""Regression checks for the reviewed run: ankles, rigid boots, arms and heading."""
import bpy,json,math,os,numpy as np
from pathlib import Path
from mathutils import Vector
ROOT=Path(__file__).resolve().parents[1]
path=Path(os.environ.get('HERO_MOTION_BLEND',str(ROOT/'outputs/hero-run.blend')))
bpy.ops.wm.open_mainfile(filepath=str(path));r=bpy.data.objects['HeroRig'];h=bpy.data.objects['InkHero'];s=bpy.context.scene
rest=np.array([v.co[:] for v in h.data.vertices]);motion=np.load(ROOT/'outputs/run.npz')
contact=np.stack((motion['foot_contacts'][:,:3].max(1)>.5,motion['foot_contacts'][:,3:].max(1)>.5),axis=1)
ankle=0;air=0;stance=0;wrist=0;boot_error=0;yaws=[];arm_quats=[];hands={side:[] for side in ('Left','Right')}
for f in range(1,91):
    s.frame_set(f)
    arm_quats.append([b.rotation_quaternion.normalized()[:] for b in r.pose.bones if b.name.endswith(('Arm','ForeArm','Hand'))])
    obj=h.evaluated_get(bpy.context.evaluated_depsgraph_get());mesh=obj.to_mesh()
    v=np.empty(len(mesh.vertices)*3);mesh.vertices.foreach_get('co',v);v=v.reshape(-1,3)
    for j,(side,sign) in enumerate((('Left',1),('Right',-1))):
        b=r.pose.bones[side+'Foot'];q=b.rotation_quaternion.normalized()
        a=math.degrees(2*math.acos(min(1,abs(q.w))));ankle=max(ankle,a)
        if contact[f-1,j]:stance=max(stance,a)
        else:air=max(air,a)
        ids=np.flatnonzero((rest[:,0]*sign>0)&(rest[:,2]<.105))
        transform=b.matrix @ b.bone.matrix_local.inverted()
        expected=rest[ids] @ np.array(transform.to_3x3()).T+np.array(transform.translation)
        boot_error=max(boot_error,float(np.abs(v[ids]-expected).max()))
        hand=r.pose.bones[side+'Hand'];q=hand.rotation_quaternion.normalized()
        wrist=max(wrist,math.degrees(2*math.acos(min(1,abs(q.w)))))
        hands[side].append((hand.head-r.pose.bones['Chest'].head)[:])
    b=r.pose.bones['Head'];front=(b.matrix.to_3x3() @ b.bone.matrix_local.to_3x3().inverted()) @ Vector((0,-1,0))
    yaws.append(math.degrees(math.atan2(front.x,-front.y)));obj.to_mesh_clear()
paths={side:np.array(value) for side,value in hands.items()}
span={side:float(p[:,1].max()-p[:,1].min()) for side,p in paths.items()}
lateral=min(float(np.abs(p[:,0]).min()) for p in paths.values())
yaw_span=max(yaws)-min(yaws)
s.frame_set(91)
arm_quats.append([b.rotation_quaternion.normalized()[:] for b in r.pose.bones if b.name.endswith(('Arm','ForeArm','Hand'))])
q=np.array(arm_quats);arm_step=float((2*np.arccos(np.clip(np.abs(np.sum(q[:-1]*q[1:],2)),-1,1))*180/np.pi).max())
passed=ankle<45.05 and air<40.1 and wrist<.1 and boot_error<1e-5 and yaw_span<10 and min(span.values())>.18 and lateral>.16 and arm_step<30
report={'status':'PASS' if passed else 'FAIL','frames':90,'max_ankle_rotation_from_bind_degrees':ankle,'stance_max_ankle_degrees':stance,'air_max_ankle_degrees':air,'rigid_boot_skin_error_m':boot_error,'max_wrist_rotation_degrees':wrist,'head_yaw_min_degrees':min(yaws),'head_yaw_max_degrees':max(yaws),'head_yaw_excursion_degrees':yaw_span,'wrist_fore_aft_span_m':span,'minimum_wrist_lateral_distance_from_chest_m':lateral,'scope':'Character-specific artistic limits, not anatomical standards. Ground contact, silhouette and cloth reviewed separately.'}
report['max_arm_joint_rotation_step_degrees']=arm_step
print(json.dumps(report,indent=2))
if 'HERO_MOTION_BLEND' not in os.environ:(ROOT/'docs/logs/hero-run-motion-check.json').write_text(json.dumps(report,indent=2)+'\n')
assert passed,'Run motion or rigid boot regression'

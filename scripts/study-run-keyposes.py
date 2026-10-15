"""Four authored side-view run poses; no replacement of the Kimodo clip."""
import bpy,json,math,numpy as np
from pathlib import Path
from mathutils import Vector,Quaternion
ROOT=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(ROOT/'outputs/tripo-run.blend'))
scene=bpy.context.scene;rig=bpy.data.objects['TripoRunRig'];hero=bpy.data.objects['TripoHero']
camera=scene.camera;camera.animation_data_clear();camera.data.ortho_scale=1.22
scene.render.resolution_x=scene.render.resolution_y=512
dest=ROOT/'.cache/run-keyposes';dest.mkdir(parents=True,exist_ok=True)
def view():
    camera.location=(2.7,0,.50);camera.rotation_euler=(Vector((0,0,.50))-camera.location).to_track_quat('-Z','Y').to_euler()
def render(path):
    view();scene.render.filepath=str(path);bpy.ops.render.render(write_still=True)
for i,f in enumerate((1,5,9,12)):
    scene.frame_set(f)
    action=rig.animation_data.action
    rig.animation_data.action=None
    # Remove progression only; same fixed camera for old and new poses.
    rig.location.x=rig.location.y=0;bpy.context.view_layer.update()
    render(dest/f'before-{i}.png')
    rig.animation_data.action=action
rig.animation_data_clear()
for b in rig.pose.bones:b.rotation_mode='QUATERNION';b.rotation_quaternion=(1,0,0,0);b.location=(0,0,0);b.scale=(1,1,1)
rest={b.name:b.matrix_local.copy() for b in rig.data.bones}
def world_rotation(name,world):
    b=rig.pose.bones[name]
    parent=b.parent.matrix.to_3x3().normalized() if b.parent else None
    relative=rest[b.parent.name].inverted()@rest[name] if b.parent else rest[name]
    local=parent.inverted()@world if parent else world
    b.rotation_quaternion=(relative.to_3x3().inverted()@local).to_quaternion()
    bpy.context.view_layer.update()
def point(name,target):
    b=rig.pose.bones[name];direction=(Vector(target)-b.head).normalized()
    rotation=rest[name].to_3x3()
    world_rotation(name,rotation.col[1].rotation_difference(direction).to_matrix()@rotation)
target_adjustments=[]
def solve(upper,lower,end,pole):
    b=rig.pose.bones[upper];origin=b.head.copy();end=Vector(end)
    delta=end-origin;distance=delta.length;l1=b.bone.length;l2=rig.pose.bones[lower].bone.length
    if distance>(l1+l2)*.97:
        target_adjustments.append(float(distance-(l1+l2)*.97))
        end=origin+delta.normalized()*(l1+l2)*.97
        delta=end-origin;distance=delta.length
    direction=delta.normalized();p=Vector(pole);p=(p-direction*p.dot(direction)).normalized()
    a=(l1*l1-l2*l2+distance*distance)/(2*distance)
    joint=origin+direction*a+p*math.sqrt(max(0,l1*l1-a*a))
    point(upper,joint);point(lower,end)
    return (rig.pose.bones[lower].tail-end).length
poses=[
    dict(label='Contact',lean=18,root=-.025,feet=[(-.12,.095),(.13,.18)],arms=[(-.17,-.12),(.11,-.185)]),
    dict(label='Support',lean=20,root=-.015,feet=[(-.015,.092),(.14,.19)],arms=[(-.12,-.15),(.11,-.18)]),
    dict(label='Push',lean=23,root=-.025,feet=[(.12,.105),(-.075,.22)],arms=[(.10,-.19),(-.17,-.12)]),
    dict(label='Flight',lean=18,root=.005,feet=[(.10,.235),(-.125,.15)],arms=[(.11,-.185),(-.17,-.12)])]
report=[]
edges=np.array([e.vertices[:] for e in hero.data.edges]);base=np.array([v.co[:] for v in hero.data.vertices])
length=np.linalg.norm(base[edges[:,0]]-base[edges[:,1]],axis=1);valid=length>.002
for i,pose in enumerate(poses):
    scene.frame_set(i+1);rig.location=(0,0,pose['root'])
    for b in rig.pose.bones:b.rotation_quaternion=(1,0,0,0)
    bpy.context.view_layer.update()
    lean=Quaternion(Vector((1,0,0)),math.radians(pose['lean'])).to_matrix()
    for n in ('Hips','Spine1','Chest','Head'):world_rotation(n,lean@rest[n].to_3x3())
    reach=[]
    for j,(side,sign) in enumerate((('Left',1),('Right',-1))):
        yaw=math.radians((7 if pose['arms'][j][0]<0 else -7)*sign)
        world_rotation(side+'Clavicle',lean@Quaternion(Vector((0,0,1)),yaw).to_matrix()@rest[side+'Clavicle'].to_3x3())
        shoulder=rig.pose.bones[side+'Arm'].head.copy()
        y,z=pose['arms'][j];hand=shoulder+Vector((sign*.035,y,z))
        reach.append(solve(side+'Arm',side+'ForeArm',hand,(sign*.25,0,-1)))
        world_rotation(side+'Hand',rig.pose.bones[side+'ForeArm'].matrix.to_3x3().normalized())
        y,z=pose['feet'][j];ankle=Vector((sign*.12,y,z-pose['root']))
        reach.append(solve(side+'UpLeg',side+'Leg',ankle,(0,-1,0)))
        pitch=math.radians(15 if i==2 and j==0 else -8 if z>.16 else 0)
        foot=Quaternion(Vector((1,0,0)),pitch).to_matrix()@rest[side+'Foot'].to_3x3()
        shin=rig.pose.bones[side+'Leg'].matrix.to_3x3().normalized()
        neutral=shin@rest[side+'Leg'].to_3x3().inverted()@rest[side+'Foot'].to_3x3()
        delta=(neutral.inverted()@foot).to_quaternion()
        if delta.w<0:delta.negate()
        if delta.angle>math.radians(35):
            delta=Quaternion((1,0,0,0)).slerp(delta,math.radians(35)/delta.angle)
            foot=neutral@delta.to_matrix()
        world_rotation(side+'Foot',foot)
    obj=hero.evaluated_get(bpy.context.evaluated_depsgraph_get());mesh=obj.to_mesh()
    points=np.array([(obj.matrix_world@v.co)[:] for v in mesh.vertices]);obj.to_mesh_clear()
    # Ground the lowest shoe without changing limb lengths; retain flight gap.
    lift=-float(points[:,2].min())+(.025 if i==3 else 0)
    rig.location.z+=lift;bpy.context.view_layer.update()
    ratios=np.linalg.norm(points[edges[:,0]]-points[edges[:,1]],axis=1)[valid]/length[valid]
    report.append(dict(pose=pose['label'],lean_degrees=pose['lean'],ik_error=max(reach),
                       target_adjustment_max_m=max(target_adjustments,default=0),
                       edge_stretch_max=float(ratios.max()),edge_stretch_p99=float(np.quantile(ratios,.99))))
    rig.keyframe_insert('location',frame=i+1)
    for b in rig.pose.bones:b.keyframe_insert('rotation_quaternion',frame=i+1)
    render(dest/f'after-{i}.png')
scene.frame_start=1;scene.frame_end=4;scene.frame_set(1)
bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'outputs/tripo-run-keyposes.blend'),compress=True)
(ROOT/'docs/logs/tripo-run-keyposes.json').write_text(json.dumps({'scope':'Four pose study, not a timed animation','poses':report},indent=2)+'\n')

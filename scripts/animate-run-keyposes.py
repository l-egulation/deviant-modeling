"""Bake an authored 0.6-second run cycle from the accepted pose study."""
import bpy,json,math,numpy as np
from pathlib import Path
from mathutils import Vector,Matrix,Quaternion
ROOT=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(ROOT/'outputs/tripo-run-keyposes.blend'))
scene=bpy.context.scene;rig=bpy.data.objects['TripoRunRig'];hero=bpy.data.objects['TripoHero']
rest={b.name:b.matrix_local.copy() for b in rig.data.bones}
parents={b.name:b.parent.name if b.parent else None for b in rig.data.bones}
relative={n:rest[p].inverted()@rest[n] if p else rest[n] for n,p in parents.items()}
names=list(rest);keys=[]
for f in range(1,5):
    scene.frame_set(f)
    keys.append((rig.location.z,{n:rig.pose.bones[n].rotation_quaternion.copy() for n in names},
                 {n:rig.pose.bones[n].matrix.to_3x3().normalized() for n in names}))
reflection=Matrix(((-1,0,0),(0,1,0),(0,0,1)))
def opposite(n):return n.replace('Left','Right') if n.startswith('Left') else n.replace('Right','Left') if n.startswith('Right') else n
def mirror(key):
    worlds={n:reflection@key[2][opposite(n)]@rest[opposite(n)].to_3x3().inverted()@reflection@rest[n].to_3x3() for n in names}
    rotations={n:(relative[n].to_3x3().inverted()@(worlds[p].inverted()@worlds[n] if p else worlds[n])).to_quaternion() for n,p in parents.items()}
    return key[0],rotations,worlds
all_keys=keys+[mirror(k) for k in keys]+[keys[0]]
times=[0,.25,.55,.8,1,1.25,1.55,1.8,2]
rig.animation_data_clear();scene.camera.animation_data_clear()
base=np.array([v.co[:] for v in hero.data.vertices]);soles={}
for side,sign in [('Left',1),('Right',-1)]:
    ids=np.flatnonzero((base[:,0]*sign>0)&(base[:,2]<.075))
    soles[side]=base[ids]-np.array(rest[side+'Foot'].translation)
def set_world(n,world):
    p=parents[n];parent=rig.pose.bones[p].matrix.to_3x3().normalized() if p else None
    q=(relative[n].to_3x3().inverted()@(parent.inverted()@world if parent else world)).to_quaternion()
    rig.pose.bones[n].rotation_quaternion=q;bpy.context.view_layer.update()
def solve(side,end):
    thigh=rig.pose.bones[side+'UpLeg'];shin=rig.pose.bones[side+'Leg'];hip=thigh.head.copy()
    delta=Vector(end)-hip;l1=thigh.bone.length;l2=shin.bone.length
    distance=min(delta.length,(l1+l2)*.985);direction=delta.normalized()
    end=hip+direction*distance
    pole=Vector((0,-1,0));pole=(pole-direction*pole.dot(direction)).normalized()
    a=(l1*l1-l2*l2+distance*distance)/(2*distance)
    knee=hip+direction*a+pole*math.sqrt(max(0,l1*l1-a*a))
    for n,origin,target in [(side+'UpLeg',hip,knee),(side+'Leg',knee,end)]:
        r=rig.pose.bones[n].matrix.to_3x3().normalized()
        set_world(n,r.col[1].rotation_difference((target-origin).normalized()).to_matrix()@r)
    return (rig.pose.bones[side+'Leg'].tail-Vector(end)).length
def coordinates():
    obj=hero.evaluated_get(bpy.context.evaluated_depsgraph_get());mesh=obj.to_mesh()
    result=np.array([(obj.matrix_world@v.co)[:] for v in mesh.vertices]);obj.to_mesh_clear();return result
speed=.9;cycle=18;records=[];anchors={};stance_positions={};ankle_angles=[]
for i in range(19):
    phase=i/9
    k=max(j for j in range(8) if times[j]<=phase) if i<18 else 7
    t=(phase-times[k])/(times[k+1]-times[k]);t=max(0,min(1,t));ease=t*t*(3-2*t)
    rig.location=(0,-speed*i/30,all_keys[k][0]*(1-ease)+all_keys[k+1][0]*ease)
    for n in names:
        rig.pose.bones[n].rotation_quaternion=all_keys[k][1][n].slerp(all_keys[k+1][1][n],ease)
    # A small counter-rotation travels naturally through the parent hierarchy.
    yaw=math.sin(i*2*math.pi/18)
    for n,angle in [('Hips',-2),('Chest',3)]:
        rig.pose.bones[n].rotation_quaternion @= Quaternion(Vector((0,1,0)),math.radians(angle)*yaw)
    bpy.context.view_layer.update()
    half=i//9;step=i%9;stance='Left' if half%2==0 else 'Right';contact=step<6
    # Keep the stance toe fixed in world space. Root moves past it; leg lengths
    # remain fixed. Reach correction lowers the pelvis before solving the leg.
    if contact:
        side=stance;foot=rig.pose.bones[side+'Foot']
        sole=soles[side]
        floor_vertices=sole[sole[:,2]<sole[:,2].min()+.002]
        pivot=Vector(floor_vertices[np.argmin(floor_vertices[:,1])])
        if step==0:
            anchors[half]=Vector((float(foot.head.x),float((rig.matrix_world@foot.head).y)-.07,0))
        pitch=math.radians(max(0,step-3)*6)
        rotation=Quaternion(Vector((1,0,0)),pitch).to_matrix()
        foot_world=rotation@rest[side+'Foot'].to_3x3()
        target=anchors[half]-(rotation@pivot)-rig.location
        hip=rig.pose.bones[side+'UpLeg'].head
        reach=sum(rig.data.bones[side+n].length for n in ('UpLeg','Leg'))*.985
        horizontal=Vector((target.x-hip.x,target.y-hip.y,0)).length
        allowed=math.sqrt(max(.0001,reach*reach-horizontal*horizontal))
        drop=max(0,hip.z-target.z-allowed)
        rig.location.z-=drop;target.z+=drop;bpy.context.view_layer.update()
        solve(side,target);set_world(side+'Foot',foot_world)
        stance_positions.setdefault(half,[]).append(list(rig.matrix_world@rig.pose.bones[side+'Foot'].head+rotation@pivot))
    # Raise the other foot as needed using its leg, avoiding a root-height pop.
    for side in ('Left','Right'):
        if contact and side==stance:continue
        foot=rig.pose.bones[side+'Foot'];foot_world=foot.matrix.to_3x3().normalized()
        target=foot.head.copy()
        for iteration in range(4):
            shin=rig.pose.bones[side+'Leg'].matrix.to_3x3().normalized()
            neutral=shin@rest[side+'Leg'].to_3x3().inverted()@rest[side+'Foot'].to_3x3()
            delta=(neutral.inverted()@foot_world).to_quaternion()
            if delta.w<0:delta.negate()
            if delta.angle>math.radians(40):
                foot_world=neutral@Quaternion((1,0,0,0)).slerp(delta,math.radians(40)/delta.angle).to_matrix()
            rotate=foot_world@rest[side+'Foot'].to_3x3().inverted()
            lowest=float((soles[side]@np.array(rotate).T)[:,2].min()+target.z+rig.location.z)
            target.z+=max(0,(.008 if contact else .025)-lowest)
            solve(side,target);set_world(side+'Foot',foot_world)
    points=coordinates();bottom=float(points[:,2].min())
    if bottom<0:rig.location.z-=bottom;bpy.context.view_layer.update()
    records.append((rig.location.copy(),{n:rig.pose.bones[n].rotation_quaternion.copy() for n in names}))
# Close the cycle explicitly, then repeat exactly five times over three seconds.
travel=Vector((0,-speed*.6,0));records[18]=(records[0][0]+travel,{n:q.copy() for n,q in records[0][1].items()})
# Smooth pelvis height periodically, then re-solve both feet at their original
# world locations. A downward offset preserves the fixed-length reach margin.
raw=np.array([r[0].z for r in records[:18]])
smoothed=raw.copy()
for iteration in range(2):
    smoothed=sum(np.roll(smoothed,k)*w for k,w in [(-2,.0625),(-1,.25),(0,.375),(1,.25),(2,.0625)])
smoothed+=min(0,float((raw-smoothed).min()))
for i in range(18):
    root,rotations=records[i];rig.location=root
    for n,q in rotations.items():rig.pose.bones[n].rotation_quaternion=q
    bpy.context.view_layer.update()
    feet={s:(rig.matrix_world@rig.pose.bones[s+'Foot'].head,
             rig.pose.bones[s+'Foot'].matrix.to_3x3().normalized()) for s in ('Left','Right')}
    rig.location.z=float(smoothed[i]);bpy.context.view_layer.update()
    for side,(position,rotation) in feet.items():
        solve(side,position-rig.location);set_world(side+'Foot',rotation)
    records[i]=(rig.location.copy(),{n:rig.pose.bones[n].rotation_quaternion.copy() for n in names})
records[18]=(records[0][0]+travel,{n:q.copy() for n,q in records[0][1].items()})
for i in range(91):
    scene.frame_set(i+1);n=i%18;lap=i//18
    root,rotations=records[n];rig.location=root+travel*lap;rig.keyframe_insert('location',frame=i+1)
    for name,q in rotations.items():
        b=rig.pose.bones[name];q=q.copy();q.make_compatible(b.rotation_quaternion);b.rotation_quaternion=q;b.keyframe_insert('rotation_quaternion',frame=i+1)
scene.frame_start=1;scene.frame_end=90;scene.render.fps=30
rig['loop_displacement']=list(travel*5);rig['run_cycle_seconds']=.6
camera=scene.camera;camera.data.ortho_scale=1.3
for f in (1,91):
    center=Vector((0,-speed*(f-1)/30,.49));camera.location=center+Vector((2.7,0,.10))
    camera.rotation_euler=Vector((-2.7,0,-.10)).to_track_quat('-Z','Y').to_euler()
    camera.keyframe_insert('location',frame=f);camera.keyframe_insert('rotation_euler',frame=f)
# Linear interpolation is essential for constant camera travel.
for owner in (rig,camera):
    action=owner.animation_data.action
    for layer in action.layers:
        for strip in layer.strips:
            for bag in strip.channelbags:
                for curve in bag.fcurves:
                    for key in curve.keyframe_points:key.interpolation='LINEAR'
scene.frame_set(1)
bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'outputs/tripo-run.blend'),compress=True)
bpy.ops.object.select_all(action='DESELECT');hero.select_set(True);rig.select_set(True);bpy.context.view_layer.objects.active=rig
scene.frame_end=91
bpy.ops.export_scene.gltf(filepath=str(ROOT/'outputs/tripo-run.glb'),use_selection=True,export_animations=True,
    export_frame_range=True,export_force_sampling=True,export_animation_mode='SCENE')
scene.frame_end=90
drift=max(float(np.ptp(np.array(samples),axis=0).max()) for samples in stance_positions.values())
(ROOT/'docs/logs/tripo-run-authored.json').write_text(json.dumps({'source':'Approved four-pose study; authored animation, not new Kimodo generation',
    'cycle_seconds':.6,'cycles':5,'speed_m_s':speed,'frames':90,'stance_toe_world_drift_before_final_grounding_m':drift,
    'scope':'Baked candidate; rendering and final deformation verification required'},indent=2)+'\n')

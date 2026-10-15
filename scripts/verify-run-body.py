"""Verify actual shoulder exchange, counter-rotation, and unchanged proportions."""
import bpy,json,math,os,subprocess
import numpy as np
from pathlib import Path
from mathutils import Vector
ROOT=Path(__file__).resolve().parents[1];BASE='6d694eb50314b145ff2e3069ad00e0e67d06167e'
before=ROOT/'.cache/hero-run-body-before.blend'
if not before.exists():before.write_bytes(subprocess.check_output(['git','show',BASE+':outputs/hero-run.blend'],cwd=ROOT))
bpy.ops.wm.open_mainfile(filepath=str(before));r=bpy.data.objects['HeroRig'];s=bpy.context.scene
rest=np.array([v.co[:] for v in bpy.data.objects['InkHero'].data.vertices]);bind={b.name:np.array(b.matrix_local) for b in r.data.bones}
lower=['Hips']+[side+part for side in ('Left','Right') for part in ('UpLeg','Leg','Foot')]
source=[]
for f in range(1,31):
    s.frame_set(f);source.append({n:r.pose.bones[n].rotation_quaternion.copy() for n in lower})
cycle=[{n:source[i][n].slerp(source[i+15][n],.5) for n in lower} for i in range(15)]
path=os.environ.get('HERO_BODY_CANDIDATE',str(ROOT/'outputs/hero-run.blend'))
bpy.ops.wm.open_mainfile(filepath=path);r=bpy.data.objects['HeroRig'];s=bpy.context.scene
mesh_error=float(np.abs(rest-np.array([v.co[:] for v in bpy.data.objects['InkHero'].data.vertices])).max())
bind_error=max(float(np.abs(m-np.array(r.data.bones[n].matrix_local)).max()) for n,m in bind.items())
shoulders=[];hips=[];chest=[];lean=[];qerror=0;foot_error=0
for i in range(91):
    s.frame_set(i+1)
    if i<90:
        shoulders.append(r.pose.bones['LeftArm'].head.y-r.pose.bones['RightArm'].head.y)
        for name,target in (('Hips',hips),('Chest',chest)):
            b=r.pose.bones[name];d=b.matrix.to_3x3() @ b.bone.matrix_local.to_3x3().inverted();front=d @ Vector((0,-1,0));target.append(math.atan2(front.x,-front.y))
            if name=='Chest':
                up=d @ Vector((0,0,1));lean.append(math.degrees(math.atan2(-up.y,up.z)))
    phase=i*5/6%15;a=int(phase);t=phase-a
    for n in lower:
        expected=cycle[a][n].slerp(cycle[(a+1)%15][n],t);actual=r.pose.bones[n].rotation_quaternion
        error=min(float(np.abs(np.array(expected)-np.array(actual)).max()),float(np.abs(np.array(expected)+np.array(actual)).max()))
        if n.endswith('Foot'):foot_error=max(foot_error,error)
        else:qerror=max(qerror,error)
corr=float(np.corrcoef(hips,chest)[0,1]);clavicles=all(n in r.data.bones for n in ('LeftClavicle','RightClavicle'))
r.animation_data_clear();r.location=(0,0,0)
for bone in r.pose.bones:bone.rotation_quaternion=(1,0,0,0)
s.view_layers[0].update()
hero=bpy.data.objects['InkHero'];obj=hero.evaluated_get(s.view_layers[0].depsgraph);mesh=obj.to_mesh()
neutral_error=float(np.abs(rest-np.array([v.co[:] for v in mesh.vertices])).max());obj.to_mesh_clear()
passed=clavicles and mesh_error<1e-7 and neutral_error<1e-6 and bind_error<1e-6 and qerror<1e-5 and foot_error<.009 and min(shoulders)<-.02 and max(shoulders)>.02 and corr<-.95 and min(lean)>8 and max(lean)<17 and r.get('run_cycle_seconds')==.6
report={'status':'PASS' if passed else 'FAIL','baseline_commit':BASE,'bones':len(r.data.bones),'rest_mesh_error_m':mesh_error,'original_bone_rest_matrix_error':bind_error,'lower_pose_error_from_phase_matched_cycle':qerror,'shoulder_front_back_difference_range_m':[min(shoulders),max(shoulders)],'pelvis_chest_yaw_correlation':corr,'chest_forward_lean_range_degrees':[min(lean),max(lean)],'cycle_seconds':r.get('run_cycle_seconds'),'scope':'Verifies torso coordination and fitted proportions. Contact, sleeve deformation, loop and visual style checked separately.'}
report['foot_quaternion_correction_error']=foot_error
report['neutral_skin_vertex_error_m']=neutral_error
print(json.dumps(report,indent=2))
if 'HERO_BODY_CANDIDATE' not in os.environ:(ROOT/'docs/logs/hero-run-body-check.json').write_text(json.dumps(report,indent=2)+'\n')
assert passed,'Shoulder coordination, cadence or fitted proportion regression'

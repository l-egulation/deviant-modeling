"""Regression checks for user-requested polish against a saved pre-polish scene."""
import bpy,numpy as np,json,math,os
from pathlib import Path
R=Path(__file__).resolve().parents[1]
base=R/os.environ.get('POLISH_BASELINE','.cache/run-before-polish.blend')
def read(path):
 bpy.ops.wm.open_mainfile(filepath=str(path));s=bpy.context.scene;r=bpy.data.objects['TripoRunRig'];h=bpy.data.objects['TripoHero'];rows=[]
 for f in range(1,91):
  s.frame_set(f);rows.append({'bones':{b.name:[list(r.matrix_world@b.head),list(r.matrix_world@b.tail)] for b in r.pose.bones},'rot':{b.name:b.matrix.to_quaternion().copy() for b in r.pose.bones},'ankles':{a:(r.matrix_world@r.pose.bones[a+'Foot'].head).copy() for a in ('Left','Right')},'angles':[180-math.degrees((r.pose.bones[a+'Arm'].tail-r.pose.bones[a+'Arm'].head).angle(r.pose.bones[a+'ForeArm'].tail-r.pose.bones[a+'ForeArm'].head)) for a in ('Left','Right')]})
 return rows,np.array([v.co[:] for v in h.data.vertices])
a,va=read(base);b,vb=read(R/'outputs/hero-mixamo-run.blend')
angles=[x for row in b for x in row['angles']];keep=['Hips','Spine1','Chest','Head']+[s+p for s in ('Left','Right') for p in ('Clavicle','Arm','Foot')]
error=max(math.degrees(a[i]['rot'][n].rotation_difference(b[i]['rot'][n]).angle) for i in range(90) for n in keep)
ankle=max((a[i]['ankles'][s]-b[i]['ankles'][s]).length for i in range(90) for s in ('Left','Right'))
assert min(angles)>110 and max(angles)<123,angles
assert error<.1,error
assert ankle<1e-4,ankle
assert np.abs(va-vb).max()==0
report={'actual_elbow_interior_range':[min(angles),max(angles)],'unchanged_body_upperarm_foot_world_rotation_max_degrees':error,'ankle_world_position_error_max_m':ankle,'rest_mesh_position_error':0,'baseline':str(base),'frames':90}
(R/'docs/logs/hero-mixamo-polish-validation.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report))

data=json.loads((R/'docs/logs/hero-mixamo-run-skeleton.json').read_text());data['previous']=[row['bones'] for row in a];data['target']=[row['bones'] for row in b];(R/'docs/logs/hero-mixamo-run-skeleton.json').write_text(json.dumps(data))

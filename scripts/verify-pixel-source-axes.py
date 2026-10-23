"""Regression: imported FBX axes must match anatomical joints before retargeting."""
import bpy,os,json
from pathlib import Path
R=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(R/os.environ.get('AXIS_INPUT','outputs/pixel-run.blend')))
a=bpy.data.objects['Motion_Raw_Source'];t=bpy.data.objects['TripoPixel_Rig'];s=bpy.context.scene
pairs={side+n:side+c for side in ['Left','Right'] for n,c in [('Arm','ForeArm'),('ForeArm','Hand'),('Leg','Shin'),('Shin','Foot'),('Foot','ToeBase')]}
rest_error=0.;pose_error=0.;target_error=0.
for n,c in pairs.items():
 direction=(a.data.bones[c].head_local-a.data.bones[n].head_local).normalized();axis=a.data.bones[n].matrix_local.to_3x3().col[1].normalized()
 rest_error=max(rest_error,(direction-axis).length)
assert rest_error<1e-4,f'Non-anatomical source rest axes: {rest_error}'
for f in range(1,91):
 s.frame_set(f);bpy.context.view_layer.update()
 for n,c in pairs.items():
  direction=(a.pose.bones[c].head-a.pose.bones[n].head).normalized();axis=a.pose.bones[n].matrix.to_3x3().col[1].normalized();pose_error=max(pose_error,(direction-axis).length)
 for side,word in [('L','Left'),('R','Right')]:
  for n,m in [('UpperArm','Arm'),('Forearm','ForeArm'),('Hand','Hand'),('Foot','Foot'),('Toe','ToeBase')]:
   x=t.pose.bones[n+'.'+side].matrix.to_3x3().col[1].normalized();y=a.pose.bones[word+m].matrix.to_3x3().col[1].normalized();target_error=max(target_error,(x-y).length)
assert pose_error<1e-4,f'Source anatomical pose error: {pose_error}'
assert target_error<1e-4,f'Target direction error: {target_error}'
report={'frames':90,'rest_axis_vector_error':rest_error,'pose_axis_vector_error':pose_error,'target_direction_vector_error':target_error,'status':'PASS'}
(R/'docs/logs/pixel-run-axis-validation.json').write_text(json.dumps(report,indent=2));print(report)

import bpy,json,math,numpy as np,os
from pathlib import Path
R=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(R/os.environ.get('POSTURE_INPUT','outputs/pixel-run.blend')))
s=bpy.context.scene;t=bpy.data.objects['TripoPixel_Rig'];a=bpy.data.objects.get('Motion_Raw_Source') or bpy.data.objects['Kimodo_Raw_Source']
def lean(v):return math.degrees(math.atan2(-v.y,v.z))
rows=[]
for f in range(1,91):
 s.frame_set(f);bpy.context.view_layer.update()
 rows.append({'frame':f,'source_hips_neck':lean(a.pose.bones['Neck1'].head-a.pose.bones['Hips'].head),'target_hips_neck':lean(t.pose.bones['Neck'].head-t.pose.bones['Hips'].head),'source_hips_chest':lean(a.pose.bones['Chest'].head-a.pose.bones['Hips'].head),'target_hips_chest':lean(t.pose.bones['Chest'].head-t.pose.bones['Hips'].head),'source_chest_head':lean(a.pose.bones['Head'].head-a.pose.bones['Chest'].head),'target_chest_head':lean(t.pose.bones['Head'].head-t.pose.bones['Chest'].head)})
summary={k:{'mean':float(np.mean([r[k] for r in rows])),'min':min(r[k] for r in rows),'max':max(r[k] for r in rows)} for k in rows[0] if k!='frame'}
rest={}
for ob in [a,t]:
 rest[ob.name]={b.name:{'head':list(b.head_local),'tail':list(b.tail_local)} for b in ob.data.bones if b.name in ['Hips','Spine','Spine1','Spine2','Chest','Neck','Neck1','Head']}
report={'forward':'-Y; positive lean is forward','summary':summary,'rest':rest,'frames':rows}
(R/'docs/logs/pixel-run-posture.json').write_text(json.dumps(report,indent=2));print(json.dumps(summary,indent=2))
if os.environ.get('POSTURE_ASSERT')=='1':
 assert summary['source_hips_neck']['min']>=0,'Source torso leans backward'
 assert summary['target_hips_neck']['min']>=0,'Retargeted torso leans backward'
 assert 5<=summary['target_hips_neck']['mean']<=22,'Target torso outside chosen forward-lean range'
 print('POSTURE REGRESSION PASS: source and target remain forward for all 90 frames')

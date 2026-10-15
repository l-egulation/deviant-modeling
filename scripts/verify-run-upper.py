"""Verify compact upper posing while preserving the accepted lower-body keys."""
import bpy,json,math,os,subprocess
import numpy as np
from pathlib import Path
from mathutils import Vector
ROOT=Path(__file__).resolve().parents[1]
BASE='759acc8f24b4e7f49d7e7b074c5bd9f1d4ab3d4d'
before=ROOT/'.cache/hero-run-upper-before.blend'
if not before.exists():
    before.parent.mkdir(parents=True,exist_ok=True)
    before.write_bytes(subprocess.check_output(['git','show',BASE+':outputs/hero-run.blend'],cwd=ROOT))
names=['Hips']+[s+p for s in ('Left','Right') for p in ('UpLeg','Leg','Foot')]
def sample(path):
    bpy.ops.wm.open_mainfile(filepath=str(path));s=bpy.context.scene;r=bpy.data.objects['HeroRig']
    roots=[];rotations=[];heads=[];lean=[];hands=[]
    for f in range(1,92):
        s.frame_set(f);roots.append(r.location[:]);rotations.append([r.pose.bones[n].rotation_quaternion[:] for n in names]);heads.append([(r.matrix_world @ r.pose.bones[n].head)[:] for n in names])
        b=r.pose.bones['Chest'];up=(b.matrix.to_3x3() @ b.bone.matrix_local.to_3x3().inverted()) @ Vector((0,0,1));lean.append(math.degrees(math.atan2(-up.y,up.z)))
        hands.append([(r.pose.bones[side+'Hand'].head-b.head)[:] for side in ('Left','Right')])
    return [np.array(a) for a in (roots,rotations,heads,lean,hands)]
a=sample(before)
path=Path(os.environ.get('HERO_UPPER_CANDIDATE',str(ROOT/'outputs/hero-run.blend')));b=sample(path)
root_error=float(np.abs(a[0]-b[0]).max());q_error=float(np.abs(a[1]-b[1]).max());head_error=float(np.abs(a[2]-b[2]).max())
lean_gain=float((b[3]-a[3]).mean());hands=b[4][:90]
spans=np.ptp(hands[:,:,1],axis=0);highest=float(hands[:,:,2].max());mean_y=float(hands[:,:,1].mean());width=float(np.abs(hands[:,:,0]).max())
passed=root_error<1e-7 and q_error<1e-7 and head_error<1e-6 and 5.9<lean_gain<6.1 and highest<-.04 and mean_y>.01 and (spans>.06).all() and (spans<.16).all() and width<.195
report={'status':'PASS' if passed else 'FAIL','baseline_commit':BASE,'frames':91,'root_location_difference_m':root_error,'lower_body_quaternion_difference':q_error,'lower_body_joint_position_difference_m':head_error,'added_forward_lean_mean_degrees':lean_gain,'highest_wrist_relative_to_chest_m':highest,'mean_wrist_rearward_offset_m':mean_y,'wrist_fore_aft_spans_m':spans.tolist(),'maximum_wrist_lateral_offset_m':width,'scope':'Art-direction and unchanged lower-body regression; visual style and cloth remain separate review.'}
print(json.dumps(report,indent=2))
if 'HERO_UPPER_CANDIDATE' not in os.environ:(ROOT/'docs/logs/hero-run-upper-check.json').write_text(json.dumps(report,indent=2)+'\n')
assert passed,'Upper-body style or accepted lower-body regression'

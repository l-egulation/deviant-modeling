"""Show the selected untouched Kimodo joints and audit BVH export and posture."""
from pathlib import Path
from fractions import Fraction
import json
import numpy as np
import av
from PIL import Image,ImageDraw
from kimodo.skeleton import SOMASkeleton77
from kimodo.exports.bvh import bvh_to_kimodo_motion
ROOT=Path(__file__).resolve().parents[1]
a=dict(np.load(ROOT/'outputs/tripo-run-source.npz',allow_pickle=False))
p=a['posed_joints'];sk=SOMASkeleton77();names=list(sk.bone_order_names);idx={n:i for i,n in enumerate(names)}
parents=sk.joint_parents.numpy()
keep={'Hips','Spine1','Spine2','Chest','Neck1','Neck2','Head','HeadEnd',
      'LeftShoulder','LeftArm','LeftForeArm','LeftHand','RightShoulder','RightArm','RightForeArm','RightHand',
      'LeftLeg','LeftShin','LeftFoot','LeftToeBase','RightLeg','RightShin','RightFoot','RightToeBase'}
decoded,fps=bvh_to_kimodo_motion(ROOT/'outputs/tripo-run-source.bvh',standard_tpose=True)
error=float(np.abs(decoded['posed_joints'].numpy()-p).max())
angles=[]
for side in ('Left','Right'):
    u=p[:,idx[side+'Arm']]-p[:,idx[side+'ForeArm']]
    v=p[:,idx[side+'Hand']]-p[:,idx[side+'ForeArm']]
    angle=np.degrees(np.arccos(np.clip((u*v).sum(1)/(np.linalg.norm(u,axis=1)*np.linalg.norm(v,axis=1)),-1,1)))
    angles.append(angle)
upper=p[:,idx['Neck1']]-p[:,idx['Hips']]
lean=np.degrees(np.arctan2(upper[:,2],upper[:,1]))
head_forward=a['global_rot_mats'][:,idx['Head'],:,2]
head_down=np.degrees(np.arctan2(-head_forward[:,1],head_forward[:,2]))
report={'frames':len(p),'fps':fps,'bvh_roundtrip_joint_max_error_m':error,
        'elbow_inside_angle_mean_degrees':float(np.mean(angles)),
        'elbow_nearly_straight_over_150_degrees_fraction':float((np.array(angles)>150).mean()),
        'hips_to_neck_forward_lean_mean_degrees':float(lean.mean()),
        'head_forward_downward_angle_mean_degrees':float(head_down.mean()),
        'scope':'Raw generated joints; no pose edits, retargeting or foot IK; horizontal camera centering only'}
(ROOT/'docs/logs/kimodo-raw-run-audit.json').write_text(json.dumps(report,indent=2)+'\n')
images=[]
for f in range(90):
    im=Image.new('RGB',(1152,512),(240,242,245));d=ImageDraw.Draw(im)
    q=p[f].copy();q[:,[0,2]]-=a['root_positions'][f,[0,2]]
    for col,label in enumerate(('SIDE','FRONT','THREE-QUARTER')):
        x0=col*384;d.text((x0+12,12),f'KIMODO RAW / {label}',fill=(20,25,30));d.text((x0+12,32),f'{f/30:.2f} s / frame {f+1}',fill=(20,25,30))
        d.line((x0,465,x0+384,465),fill=(150,155,160),width=1)
        def xy(j):
            x,y,z=q[j]
            horizontal=-z if col==0 else -x if col==1 else (x-z)*.7071
            return x0+192+float(horizontal)*190,465-float(y)*190
        for j,n in enumerate(names):
            if n not in keep or parents[j]<0:continue
            color=(215,65,65) if n.startswith('Left') else (45,110,220) if n.startswith('Right') else (35,40,50)
            d.line((xy(int(parents[j])),xy(j)),fill=color,width=5)
        for n in keep.intersection(idx):
            x,y=xy(idx[n]);d.ellipse((x-3,y-3,x+3,y+3),fill=(30,35,40))
        x,y=xy(idx['Head']);d.ellipse((x-12,y-14,x+12,y+14),outline=(35,40,50),width=2)
    images.append(im)
path=ROOT/'outputs/kimodo-run-source-preview.mp4'
with av.open(str(path),'w') as c:
    s=c.add_stream('libx264',rate=30);s.width=1152;s.height=512;s.pix_fmt='yuv420p';s.options={'crf':'18'}
    for i,im in enumerate(images):
        frame=av.VideoFrame.from_ndarray(np.array(im),format='rgb24');frame.pts=i;frame.time_base=Fraction(1,30)
        for packet in s.encode(frame):c.mux(packet)
    for packet in s.encode():c.mux(packet)
with av.open(str(path)) as c:assert len(list(c.decode(video=0)))==90
images[15].save(ROOT/'outputs/kimodo-run-source-views.png')
small=[im.resize((864,384),Image.Resampling.LANCZOS) for im in images]
small[0].save(ROOT/'outputs/kimodo-run-source-preview.gif',save_all=True,append_images=small[1:],duration=[30,30,40]*30,loop=0)
print(json.dumps(report,indent=2))

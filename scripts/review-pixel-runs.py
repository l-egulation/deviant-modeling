"""Preview untouched Kimodo candidates and report prompt-related measurements."""
import json,math
from pathlib import Path
import numpy as np
from PIL import Image,ImageDraw
from kimodo.skeleton import SOMASkeleton77
ROOT=Path(__file__).resolve().parents[1];sk=SOMASkeleton77()
names=list(sk.bone_order_names);indices={n:i for i,n in enumerate(names)}
parents=sk.joint_parents.numpy();kept={'Hips','Spine1','Spine2','Chest','Neck1','Neck2','Head','HeadEnd',
    'LeftShoulder','LeftArm','LeftForeArm','LeftHand','RightShoulder','RightArm','RightForeArm','RightHand',
    'LeftLeg','LeftShin','LeftFoot','LeftToeBase','RightLeg','RightShin','RightFoot','RightToeBase'}
paths=sorted((ROOT/'.cache/pixel-run/generated').glob('*.npz'));assert len(paths)==2,paths
records=[];movies=[];sheet=Image.new('RGB',(1536,768),'white');draw=ImageDraw.Draw(sheet)
for row,path in enumerate(paths):
    data=dict(np.load(path,allow_pickle=False));p=data['posed_joints'];root=data['root_positions']
    assert len(p)==90, f'Expected one 3-second segment, got {len(p)} frames'
    hands=p[:,[indices['LeftHand'],indices['RightHand']],1]
    hip=p[:,indices['Hips'],1];chest=p[:,indices['Chest'],1]
    shoulders=p[:,indices['LeftShoulder'],2]-p[:,indices['RightShoulder'],2]
    travel=float(np.linalg.norm((root[-1]-root[0])[[0,2]]))
    upper=p[:,indices['Chest']]-p[:,indices['Hips']]
    lean=np.degrees(np.arctan2(upper[:,2],upper[:,1]))
    record={'candidate':path.name,'frames':len(p),'forward_distance_m':travel,'mean_speed_m_s':travel/((len(p)-1)/30),
       'hands_above_chest_fraction':float((hands>chest[:,None]).mean()),
       'hand_height_above_hips_mean_m':float((hands-hip[:,None]).mean()),
       'shoulder_front_back_difference_span_m':float(np.ptp(shoulders)),
       'torso_forward_lean_mean_degrees':float(lean.mean()),'all_finite':bool(np.isfinite(p).all())}
    records.append(record);images=[]
    for f in range(90):
        im=Image.new('RGB',(384,384),(240,242,245));d=ImageDraw.Draw(im)
        d.text((12,10),f'Kimodo RAW / candidate {row+1} / {f/30:.2f}s',fill=(20,25,30))
        d.line((0,350,384,350),fill=(130,135,140),width=1)
        centered=p[f].copy();centered[:,[0,2]]-=root[f,[0,2]]
        def xy(i):return (192+float(centered[i,2])*150,350-float(centered[i,1])*150)
        for j,n in enumerate(names):
            if n not in kept or parents[j]<0:continue
            color=(220,65,65) if n.startswith('Left') else (45,115,225) if n.startswith('Right') else (40,45,55)
            d.line((xy(int(parents[j])),xy(j)),fill=color,width=4)
        for n in ('LeftHand','RightHand','LeftFoot','RightFoot'):
            x,y=xy(indices[n]);d.ellipse((x-4,y-4,x+4,y+4),fill=(20,25,30))
        images.append(im)
    movies.append(images)
    for col,f in enumerate((5,15,25,35)):
        sheet.paste(images[f],(col*384,row*384))
sheet.save(ROOT/'outputs/pixel-run-candidates.png')
combined=[]
for f in range(90):
    im=Image.new('RGB',(768,384));im.paste(movies[0][f],(0,0));im.paste(movies[1][f],(384,0));combined.append(im)
combined[0].save(ROOT/'outputs/pixel-run-candidates.gif',save_all=True,append_images=combined[1:],duration=[30,30,40]*30,loop=0)
(ROOT/'docs/logs/pixel-run-candidates.json').write_text(json.dumps(records,indent=2)+'\n')
print(json.dumps(records,indent=2))

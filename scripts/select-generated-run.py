"""Preserve one selected, unedited Kimodo sample and derive contact metadata."""
import sys,json,shutil
from pathlib import Path
import numpy as np
from kimodo.skeleton import SOMASkeleton77
ROOT=Path(__file__).resolve().parents[1]
paths=sorted((ROOT/'.cache/fresh-run/single').glob('*.npz'))
selected=paths[int(sys.argv[1])]
for suffix in ('.npz','.bvh'):
    shutil.copyfile(selected.with_suffix(suffix),ROOT/f'outputs/tripo-run-source{suffix}')
a=dict(np.load(selected,allow_pickle=False));sk=SOMASkeleton77();p=a['posed_joints'][:,sk.foot_joint_idx]
speed=np.linalg.norm(np.gradient(p[:,:,[0,2]],axis=0)*30,axis=-1)
contacts=(a['foot_contacts']>.5)|((p[:,:,1]<.025)&(speed<.6))
contacts[1:-1]|=contacts[:-2]&contacts[2:]
a['foot_contacts']=contacts.astype('float32')
a['foot_clearance']=np.maximum(0,np.stack((p[:,:3,1].min(1),p[:,3:,1].min(1)),axis=1)).astype('float32')
np.savez(ROOT/'.cache/fresh-run/contact-motion.npz',**a)
np.savez(ROOT/'outputs/tripo-run-contact.npz',foot_contacts=a['foot_contacts'],foot_clearance=a['foot_clearance'])
report={'selected':selected.name,'source_frames':len(p),'preserved_raw_source':True,
        'changed_motion_rotations':False,'changed_timing':False,'loop_created':False,
        'contact_metadata':'Classifier OR low slow toe; close one-frame holes; raw source retained',
        'air_frames':int((~contacts.any(1)).sum())}
(ROOT/'docs/logs/tripo-run-new-selection.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report))

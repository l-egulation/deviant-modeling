"""Select a generated run and make a phase-continuous three-second source loop."""
import json,shutil
from pathlib import Path
import numpy as np
import torch
from scipy.spatial.transform import Rotation
from kimodo.skeleton import SOMASkeleton77
from kimodo.exports.bvh import motion_to_bvh

ROOT=Path(__file__).resolve().parents[1]
sk=SOMASkeleton77();feet=sk.foot_joint_idx
body=[i for i,n in enumerate(sk.bone_order_names) if n in ('Hips','Spine1','Spine2','Chest','Neck1','Head','LeftArm','LeftForeArm','RightArm','RightForeArm','LeftLeg','LeftShin','LeftFoot','RightLeg','RightShin','RightFoot')]
def signs(q):
    q=q.copy()
    for i in range(1,len(q)):
        q[i][np.sum(q[i-1]*q[i],axis=-1)<0]*=-1
    return q
def periodic(data,t):
    n=len(data);i=np.floor(t).astype(int);u=(t-i).reshape((-1,)+(1,)*(data.ndim-1))
    a,b,c,d=[data[(i+k)%n] for k in (-1,0,1,2)]
    return .5*((2*b)+(-a+c)*u+(2*a-5*b+4*c-d)*u*u+(-a+3*b-3*c+d)*u*u*u)
def contact_estimate(a):
    p=a['posed_joints'][:,feet]
    speed=np.linalg.norm(np.gradient(p[:,:,[0,2]],axis=0)*30,axis=-1)
    result=(a['foot_contacts']>.5)|((p[:,:,1]<.025)&(speed<.6))
    # Close one-frame detection holes; keep real aerial intervals intact.
    result[1:-1]|=result[:-2]&result[2:]
    return result
choices=[];candidates=[]
for path in sorted((ROOT/'.cache/run-candidates/run').glob('*.npz')):
    a=dict(np.load(path,allow_pickle=False));q=signs(Rotation.from_matrix(a['local_rot_mats'].reshape(-1,3,3)).as_quat().reshape(90,77,4))
    contacts=contact_estimate(a);lr=np.stack([contacts[:,:3].any(1),contacts[:,3:].any(1)],axis=1)
    found=[]
    for start in range(4,46):
        for period in range(14,40):
            end=start+period
            if end+1>=90 or lr[start].any() or lr[end].any():continue
            if (lr[start:end].sum(0)<2).any() or (~lr[start:end].any(1)).sum()<2:continue
            dots=np.abs(np.sum(q[start,body]*q[end,body],axis=-1))
            angle=float(np.mean(2*np.arccos(np.clip(dots,-1,1))))
            v0=a['posed_joints'][start+1,body]-a['posed_joints'][start,body]
            v1=a['posed_joints'][end+1,body]-a['posed_joints'][end,body]
            score=angle+float(np.mean(np.linalg.norm(v1-v0,axis=-1)))*2
            found.append((score,start,period,angle))
    assert found,f'No complete running stride in {path}'
    best=min(found)
    candidates.append({'file':path.name,'best_cycle_score':best[0],'start_frame':best[1],'period_frames':best[2],'endpoint_mean_angle_degrees':best[3]*180/np.pi,'inferred_air_frames':int((~lr.any(1)).sum()),'raw_classifier_air_frames':int((a['foot_contacts'].max(1)<.5).sum())})
    choices.append((best[0],path,a,q,contacts,best))
_,selected,a,q,contacts,(_,start,n,angle)=min(choices,key=lambda c:c[0])
assert angle<.25,f'Cycle endpoints too different: {angle}'
segment=q[start:start+n+1].copy();u=np.linspace(0,1,n+1)
for j in range(77):
    error=Rotation.from_quat(segment[-1,j]).inv()*Rotation.from_quat(segment[0,j])
    correction=Rotation.from_rotvec(u[:,None]*error.as_rotvec()[None,:])
    segment[:,j]=(Rotation.from_quat(segment[:,j])*correction).as_quat()
segment=signs(segment)[:-1]
cycles=max(1,round(90/n));period=90/cycles;t=np.arange(90)*n/period
qout=periodic(segment,t);qout/=np.linalg.norm(qout,axis=-1,keepdims=True)
local=Rotation.from_quat(qout.reshape(-1,4)).as_matrix().reshape(90,77,3,3).astype('float32')
original_root=a['root_positions'][start:start+n+1]
delta=original_root[-1]-original_root[0]
residual=original_root-original_root[0]-u[:,None]*delta
step=delta.copy();step[1]=0
roots=(original_root[0]+periodic(residual[:-1],t)+(np.arange(90)/period)[:,None]*step).astype('float32')
global_rots,positions,_=sk.fk(torch.from_numpy(local),torch.from_numpy(roots))
sample=np.rint(t).astype(int)%n
new_contacts=contacts[start+sample].astype('float32')
heading=np.arctan2(global_rots.numpy()[:,sk.root_idx,0,2],global_rots.numpy()[:,sk.root_idx,2,2])
smooth=roots.copy();smooth[:,1]=0
foot_y=positions.numpy()[:,feet,1]
clearance=np.maximum(0,np.stack((foot_y[:,:3].min(1),foot_y[:,3:].min(1)),axis=1))
out=dict(local_rot_mats=local,global_rot_mats=global_rots.numpy(),posed_joints=positions.numpy(),root_positions=roots,smooth_root_pos=smooth,foot_contacts=new_contacts,global_root_heading=np.stack((np.cos(heading),np.sin(heading)),axis=1).astype('float32'),loop_displacement=(step*cycles).astype('float32'))
out['foot_clearance']=clearance.astype('float32')
for key,value in out.items():assert np.isfinite(value).all(),key
np.savez(ROOT/'outputs/run.npz',**out)
(ROOT/'outputs/run.bvh').write_text(motion_to_bvh(torch.from_numpy(local),torch.from_numpy(roots),skeleton=sk,fps=30,standard_tpose=True))
shutil.copyfile(selected,ROOT/'outputs/run-source.npz');shutil.copyfile(selected.with_suffix('.bvh'),ROOT/'outputs/run-source.bvh')
report={'selected':selected.name,'candidates':candidates,'cycle_start_frame':start,'cycle_source_frames':n,'output_cycles':cycles,'output_period_frames':period,'cadence_time_scale':n/period,'duration_seconds':3,'frames':90,'loop_displacement_m':out['loop_displacement'].tolist(),'source_endpoint_mean_angle_degrees':angle*180/np.pi,'output_air_frames':int((new_contacts.max(1)<.5).sum()),'contact_method':'Classifier OR near-ground slow toe; close one-frame holes. Source exports are preserved separately.','loop_method':'Select full stride with matching pose and velocity; close small local-rotation drift; periodic cubic unit-quaternion sampling; preserve linear travel.'}
(ROOT/'docs/logs/run-selection.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))

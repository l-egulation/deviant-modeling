import bpy, numpy as np, json
from pathlib import Path
R=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(R/'outputs/tripo-pixel-shaped.blend'))
o=next(o for o in bpy.context.scene.objects if o.type=='MESH')
dg=bpy.context.evaluated_depsgraph_get(); ev=o.evaluated_get(dg)
p=np.array([tuple(ev.matrix_world@v.co) for v in ev.data.vertices])
raw=np.array([tuple(o.matrix_world@v.co) for v in o.data.vertices])
d=np.load(R/'outputs/tripo-pixel-inspection.npz')
print('OBJECT',o.name,'MATRIX',o.matrix_world,'RAW_NPZ_ERROR',np.max(np.abs(raw-d['xyz'])))
print('BOUNDS',p.min(0),p.max(0))
for za,zb in [(0,.05),(.08,.11),(.14,.17),(.20,.23),(.26,.29),(.35,.38),(.50,.53),(.55,.58)]:
 for side in [-1,1]:
  q=p[(p[:,2]>za)&(p[:,2]<zb)&(p[:,0]*side>0)]
  if len(q):print('SLICE',za,zb,side,len(q),np.quantile(q,[0,.5,1],axis=0).tolist())
np.savez(R/'.cache/pixel-rig-inspection.npz',xyz=p,colors=d['colors'])

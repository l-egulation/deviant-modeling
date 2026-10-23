import bpy,numpy as np
from pathlib import Path
R=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(R/'outputs/tripo-pixel-rig.blend'))
h=bpy.data.objects['TripoPixel_Character'];s=bpy.context.scene
p=np.array([v.co[:] for v in h.data.vertices]);e=np.array([x.vertices[:] for x in h.data.edges]);base=np.linalg.norm(p[e[:,0]]-p[e[:,1]],axis=1)
for f in [21,41]:
 s.frame_set(f);bpy.context.view_layer.update();ev=h.evaluated_get(bpy.context.evaluated_depsgraph_get());q=np.array([v.co[:] for v in ev.data.vertices]);ratio=np.linalg.norm(q[e[:,0]]-q[e[:,1]],axis=1)/np.maximum(base,1e-10);ratio[base<1e-4]=0
 for k in np.argsort(ratio)[-8:]:print('BAD',f,float(ratio[k]),float(base[k]),p[e[k]].tolist())

import bpy,numpy as np
from pathlib import Path
R=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(R/'outputs/tripo-pixel-working.blend'))
o=next(o for o in bpy.context.scene.objects if o.type=='MESH'); m=o.data
im=next(i for i in bpy.data.images if 'basecolor' in i.name)
p=np.array(im.pixels[:],dtype=np.float32).reshape(im.size[1],im.size[0],4)
c=np.zeros((len(m.vertices),4)); n=np.zeros(len(m.vertices))
for loop,uv in zip(m.loops,m.uv_layers.active.data):
    u,v=uv.uv; x=int(u*im.size[0])%im.size[0]; y=int(v*im.size[1])%im.size[1]
    c[loop.vertex_index]+=p[y,x]; n[loop.vertex_index]+=1
c/=np.maximum(n[:,None],1)
xyz=np.array([tuple(o.matrix_world@v.co) for v in m.vertices])
np.savez(R/'outputs/tripo-pixel-inspection.npz',xyz=xyz,colors=c)
print(o.matrix_world)

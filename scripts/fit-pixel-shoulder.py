"""Compare smooth shoulder support fields on unchanged anatomy, with exact DQ skinning."""
import bpy,numpy as np,json,sys,itertools
from pathlib import Path
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'scripts'))
from pixel_skin import skin_fields
bpy.ops.wm.open_mainfile(filepath=str(R/'outputs/tripo-pixel-rig.blend'))
h=bpy.data.objects['TripoPixel_Character'];rig=bpy.data.objects['TripoPixel_Rig'];s=bpy.context.scene
for m in list(h.modifiers):
 if m.type=='CORRECTIVE_SMOOTH':h.modifiers.remove(m)
p=np.array([v.co[:] for v in h.data.vertices]);edges=np.array([e.vertices[:] for e in h.data.edges]);base=np.linalg.norm(p[edges[:,0]]-p[edges[:,1]],axis=1);valid=base>1e-4
regions=np.array([next(h.vertex_groups[g.group].name[7:] for g in v.groups if h.vertex_groups[g.group].name.startswith('Region_')) for v in h.data.vertices])
names=[b.name for b in rig.data.bones if b.use_deform]
poses=[]
for f in [21,61,101]:
 s.frame_set(f);bpy.context.view_layer.update();qr=[];qd=[]
 for n in names:
  mat=rig.pose.bones[n].matrix@rig.data.bones[n].matrix_local.inverted();r=np.array(mat.to_quaternion());t=np.array(mat.translation)
  if r[0]<0:r=-r
  qr.append(r);qd.append(np.r_[-.5*np.dot(t,r[1:]),.5*(r[0]*t+np.cross(t,r[1:]))])
 poses.append((np.array(qr),np.array(qd)))
def deform(W,pose):
 qr,qd=pose;r=W@qr;d=W@qd;norm=np.linalg.norm(r,axis=1);r/=norm[:,None];d/=norm[:,None];rv=r[:,1:];rw=r[:,0,None]
 trans=2*(rw*d[:,1:]-d[:,0,None]*rv+np.cross(rv,d[:,1:]))
 return p+2*np.cross(rv,np.cross(rv,p)+rw*p)+trans
# Verify the analytic evaluator against Blender before comparing fields.
W=np.zeros((len(p),len(names)))
for v in h.data.vertices:
 for g in v.groups:
  n=h.vertex_groups[g.group].name
  if n in names:W[v.index,names.index(n)]=g.weight
q=np.array([v.co[:] for v in h.evaluated_get(bpy.context.evaluated_depsgraph_get()).data.vertices])
error=float(np.abs(deform(W,poses[-1])-q).max());print('DQ evaluator error',error,flush=True);assert error<1e-5
results=[]
for a,b,lo,hi in itertools.product([.015,.035,.055],[.18,.21,.24],[.20,.25,.30],[.47,.50,.53]):
 W=skin_fields(p,regions,names,(a,b,lo,hi));peaks=[]
 for pose in poses:
  q=deform(W,pose);ratios=np.linalg.norm(q[edges[:,0]]-q[edges[:,1]],axis=1)[valid]/base[valid];peaks.append(float(ratios.max()))
 results.append({'shoulder':[a,b,lo,hi],'max':max(peaks),'poses':peaks})
results.sort(key=lambda r:r['max']);(R/'docs/logs/pixel-shoulder-fit.json').write_text(json.dumps({'evaluator_error_m':error,'candidates':results},indent=2));print(json.dumps(results[:5]),flush=True)

"""Local sleeve/upper-robe geometry and explicit garment material boundaries."""
import numpy as np
def smooth(a,b,x):
 t=np.clip((x-a)/(b-a),0,1);return t*t*(3-2*t)
def regions(obj):
 return np.array([next(obj.vertex_groups[g.group].name[7:] for g in v.groups if obj.vertex_groups[g.group].name.startswith('Region_')) for v in obj.data.vertices])
def repair(obj,rig):
 mesh=obj.data;p=np.array([v.co[:] for v in mesh.vertices]);tags=regions(obj);delta=np.zeros_like(p)
 for side,sign in [('L',1),('R',-1)]:
  b=rig.data.bones['UpperArm.'+side];a=np.array(b.head_local);end=np.array(rig.data.bones['Hand.'+side].head_local)
  axis=end-a;t=np.clip((p-a)@axis/np.dot(axis,axis),0,1);center=a+t[:,None]*axis
  weight=(tags=='Arm.'+side)*smooth(.12,.23,sign*(p[:,0]-.075))
  # Narrow the sleeve cross-section, not the arm length or skeleton.
  radial=p-center;radial-=((radial@axis)/np.dot(axis,axis))[:,None]*axis
  delta-=.16*weight[:,None]*radial
 # A shallow waist indentation below the shoulder and above the free robe hem.
 waist=(tags=='Robe')*smooth(.35,.40,p[:,2])*(1-smooth(.47,.52,p[:,2]))*smooth(.045,.11,abs(p[:,0]-.075))
 delta[:,0]-=.012*waist*np.sign(p[:,0]-.075)
 # Shared boundaries remain coincident, including split UV/semantic vertices.
 _,inv=np.unique(np.round(p,6),axis=0,return_inverse=True);count=np.bincount(inv)
 avg=np.stack([np.bincount(inv,weights=delta[:,j])/count for j in range(3)],axis=1);delta=avg[inv]
 if mesh.shape_keys:
  for key in mesh.shape_keys.key_blocks:
   q=np.array([v.co[:] for v in key.data])+delta;key.data.foreach_set('co',q.astype('float32').ravel())
 else: mesh.vertices.foreach_set('co',(p+delta).astype('float32').ravel())
 mesh.update()
 return {'moved_vertices':int((np.linalg.norm(delta,axis=1)>1e-6).sum()),'max_displacement_m':float(np.linalg.norm(delta,axis=1).max()),'hood_max_displacement_m':float(np.linalg.norm(delta[tags=='Hood'],axis=1).max()),'bone_lengths_changed':False}
def clean_materials(obj,old):
 tags=regions(obj);p=np.array([v.co[:] for v in obj.data.vertices]);result=[]
 for face,label in zip(obj.data.polygons,old):
  ids=list(face.vertices);tag=tags[ids[0]];x,y,z=p[ids].mean(0)
  if tag=='Robe':label=0
  elif tag.startswith('Arm.'):
   # One clean sleeve opening in the original T pose. 0 ivory, 1 dark.
   label=1 if abs(x-.075)>.285 else 0
  elif tag.startswith('Leg.'):
   # The ankle trim is a continuous band rather than texture fragments.
   label=3 if .095<z<.140 else 1
  elif tag=='Scarf':label=3 if .06<x<.13 and y<-.125 and .47<z<.54 else 2
  result.append(label)
 return result

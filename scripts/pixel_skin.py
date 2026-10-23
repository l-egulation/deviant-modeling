"""Semantic garment islands and anatomical skin fields for the actual Tripo surface."""
import bpy
import numpy as np

def smooth(a,b,v):
 t=np.clip((v-a)/(b-a),0,1);return t*t*(3-2*t)

def separate_surface(source,colors):
 p=np.array([v.co[:] for v in source.vertices]);faces=[list(f.vertices) for f in source.polygons]
 labels=[]
 for ids in faces:
  x,y,z=p[ids].mean(0);c=colors[ids].mean(0)
  # Whole surface islands, not texture-dependent skin weights.
  if z>.615:label='Hood'
  elif (c[2]-c[0]>.09 and c[1]>.15) or (x<-.29 and y>.035) or (.06<x<.13 and y<-.125 and .47<z<.54):label='Scarf'
  elif z<.29:
   side='L' if x>.09 else 'R'
   # Leg cores; the robe shell in front/behind them remains on the torso.
   cx=np.interp(z,[.095,.205,.32],[.190,.173,.137] if side=='L' else [.002,.010,.032])
   cy=-.04 if side=='L' else .005
   core=((x-cx)/.065)**2+((y-cy)/.065)**2<1
   label='Leg.'+side if z<.195 or core else 'Robe'
  elif z<.57 and ((x>.185 and y<.055) or (x<-.035 and y<.075)) and z>.35:
   label='Arm.L' if x>.075 else 'Arm.R'
  else:label='Robe'
  labels.append(label)
 # Duplicate interface vertices: independently moving cloth must not bridge to a leg.
 lookup={};coords=[];original=[];regions=[];newfaces=[]
 for ids,label in zip(faces,labels):
  row=[]
  for i in ids:
   key=(i,label)
   if key not in lookup:
    lookup[key]=len(coords);coords.append(p[i]);original.append(i);regions.append(label)
   row.append(lookup[key])
  newfaces.append(row)
 m=bpy.data.meshes.new('Tripo semantic garment islands');m.from_pydata(coords,[],newfaces);m.update()
 for mat in source.materials:m.materials.append(mat)
 uv=m.uv_layers.new(name=source.uv_layers.active.name)
 for dst,src in zip(m.polygons,source.polygons):
  dst.use_smooth=src.use_smooth;dst.material_index=src.material_index
  for a,b in zip(dst.loop_indices,src.loop_indices):uv.data[a].uv=source.uv_layers.active.data[b].uv
 return m,np.array(original),np.array(regions),labels

def skin_fields(p,regions,names,shoulder=(.055,.24,.25,.50)):
 W=np.zeros((len(p),len(names)));x,y,z=p.T
 def add(n,w):W[:,names.index(n)]+=w
 # Robe remains torso-bound, including the hem and its lining.
 head=smooth(.595,.65,z);neck=smooth(.545,.585,z)*(1-head)
 chest=smooth(.395,.49,z)*(1-head-neck);spine=smooth(.32,.40,z)*(1-head-neck-chest)
 hips=1-head-neck-chest-spine
 for n,w in [('Head',head),('Neck',neck),('Chest',chest),('Spine',spine),('Hips',hips)]:add(n,w)
 for side,sgn in [('L',1),('R',-1)]:
  # A continuous shoulder field on both sides of the sleeve/torso seam.
  # The split is an editing boundary, not an opening at the armpit.
  eligible=(regions=='Arm.'+side)|((regions=='Robe')&((x-.075)*sgn>0))
  dist=sgn*(x-.075)
  amount=eligible*smooth(shoulder[0],shoulder[1],dist)*smooth(shoulder[2],shoulder[3],z)*(1-smooth(.54,.59,z))
  W*=1-amount[:,None]
  dist=sgn*(x-.075);fore=smooth(.17,.26,dist)
  hand=smooth(.29,.34,dist) if side=='L' else smooth(.275,.33,dist)
  add('UpperArm.'+side,amount*(1-fore))
  add('Forearm.'+side,amount*fore*(1-hand));add('Hand.'+side,amount*fore*hand)
  ids=regions=='Leg.'+side;W[ids]=0
  thigh=smooth(.17,.24,z);foot=1-smooth(.075,.135,z)
  add('Thigh.'+side,ids*thigh);add('Shin.'+side,ids*(1-thigh)*(1-foot));add('Foot.'+side,ids*(1-thigh)*foot)
 ids=regions=='Scarf';W[ids]=0;add('Neck',ids.astype(float))
 ids=regions=='Hood';W[ids]=0;add('Head',ids.astype(float))
 W/=W.sum(1)[:,None]
 return W

"""Localized shape edit of the actual Tripo mesh, retaining UVs and topology."""
import bpy, math, json
import numpy as np
from pathlib import Path
from mathutils import Vector
R=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(R/'outputs/tripo-pixel-working.blend'))
o=next(o for o in bpy.context.scene.objects if o.type=='MESH')
d=np.load(R/'outputs/tripo-pixel-inspection.npz'); p=d['xyz']; colors=d['colors']
assert len(p)==len(o.data.vertices)
# Shape keys preserve the reduced Tripo baseline and make both edits reversible.
if o.data.shape_keys: o.shape_key_clear()
o.shape_key_add(name='Tripo baseline')
hood=o.shape_key_add(name='Hood tip toward back')
scarf=o.shape_key_add(name='Scarf broad fold and twist')
def smooth(a,b,v):
    t=np.clip((v-a)/(b-a),0,1); return t*t*(3-2*t)
x,y,z=p.T
# Smooth angular remap on the rear/side hood. Front face aperture stays fixed.
theta=np.mod(np.arctan2(y,x),2*math.pi)
ang=np.rad2deg(theta)
knots=np.array([0,60,165,215,240,270,360.])
targets=np.array([0,45,90,190,240,270,360.])
# Monotone cubic mapping avoids the sharp derivative changes of linear sectors.
width=np.diff(knots); slope=np.diff(targets)/width
deriv=np.empty(len(knots)); deriv[0]=deriv[-1]=1
for j in range(1,len(knots)-1):
    a=2*width[j]+width[j-1]; b=width[j]+2*width[j-1]
    deriv[j]=(a+b)/(a/slope[j-1]+b/slope[j])
idx=np.clip(np.searchsorted(knots,ang)-1,0,len(knots)-2)
u=(ang-knots[idx])/width[idx]
mapped=(2*u**3-3*u*u+1)*targets[idx]+(u**3-2*u*u+u)*width[idx]*deriv[idx]+(-2*u**3+3*u*u)*targets[idx+1]+(u**3-u*u)*width[idx]*deriv[idx+1]
weight=smooth(.64,.73,z)
delta=np.deg2rad(mapped-ang)*weight
hp=p.copy(); hp[:,0]=x*np.cos(delta)-y*np.sin(delta); hp[:,1]=x*np.sin(delta)+y*np.cos(delta)
# Add depth to the rear hood without inflating the face rim into a round toy.
hp[:,1]+=.025*smooth(.01,.10,y)*smooth(.65,.76,z)*(1-smooth(.90,.98,z))
teal=smooth(.08,.19,colors[:,2]-colors[:,0])*smooth(.15,.30,colors[:,1])
tail=teal*smooth(.06,.20,-x)*smooth(.0,.055,y)*smooth(.22,.29,z)*(1-smooth(.55,.60,z))
t=np.clip((-x-.06)/.40,0,1)
sp=p.copy()
sp[:,1]+=tail*(.11*np.sin(t*math.pi*.85)+.8*(z-(.56-.20*t))*np.sin(t*math.pi))
sp[:,0]+=tail*.035*t
sp[:,2]+=tail*.025*np.sin(t*math.pi)
# Average coincident UV split vertices to avoid positional cracks along seams.
_,inv=np.unique(np.round(p,6),axis=0,return_inverse=True)
counts=np.bincount(inv)
for arr,key in [(hp,hood),(sp,scarf)]:
    disp=arr-p
    avg=np.stack([np.bincount(inv,weights=disp[:,j])/counts for j in range(3)],axis=1)
    arr[:]=p+avg[inv]
    for v,co in zip(key.data,arr): v.co=o.matrix_world.inverted()@Vector(co)
    key.value=1
robe=(z>.25)&(z<.56)&(colors[:,0]>.5)&(colors[:,1]>.4)
robe_delta=float(np.linalg.norm((hp-p+sp-p)[robe],axis=1).max())
assert robe_delta<1e-6, 'Ivory robe changed unexpectedly'
assert np.isfinite(hp).all() and np.isfinite(sp).all()
report={'source':'Tripo H3.1 reduced working mesh','hood_vertices_moved':int((np.linalg.norm(hp-p,axis=1)>1e-5).sum()),'scarf_vertices_moved':int((np.linalg.norm(sp-p,axis=1)>1e-5).sum()),'hood_tip_before':p[np.argmin(np.where(z>.69,x,999))].tolist(),'hood_tip_after':hp[np.argmin(np.where(z>.69,x,999))].tolist(),'cloth_simulation':False,'robe_geometry_changed':False,'ivory_robe_max_displacement':robe_delta,'topology_preserved':True}
(R/'docs/logs/tripo-pixel-shape.json').write_text(json.dumps(report,indent=2))
scene=bpy.context.scene; cam=scene.camera; center=Vector((0,0,.489395))
cam.location=center+Vector((2.12,-2.12,0))
cam.rotation_euler=(center-cam.location).to_track_quat('-Z','Y').to_euler()
bpy.ops.wm.save_as_mainfile(filepath=str(R/'outputs/tripo-pixel-shaped.blend'),compress=True)
for state,val in [('before',0),('after',1)]:
    hood.value=scarf.value=val
    for angle,label in [(0,'front'),(90,'side'),(135,'rear-oblique'),(180,'back')]:
        a=math.radians(angle); cam.location=center+Vector((math.sin(a)*3,-math.cos(a)*3,0))
        cam.rotation_euler=(center-cam.location).to_track_quat('-Z','Y').to_euler()
        scene.render.filepath=str(R/f'outputs/tripo-pixel-shape-{state}-{label}.png')
        bpy.ops.render.render(write_still=True)
print(json.dumps(report))

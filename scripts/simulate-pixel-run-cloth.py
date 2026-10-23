"""Independent world-space robe/scarf cloth and acceleration-driven hood on Kimodo run."""
import bpy,bmesh,numpy as np,json,math,sys
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'scripts'))
from pixel_cloth_solver import Cloth,grid_binding
bpy.ops.wm.open_mainfile(filepath=str(R/'outputs/pixel-run.blend'))
s=bpy.context.scene;rig=bpy.data.objects['TripoPixel_Rig'];h=bpy.data.objects['TripoPixel_Character']
p=np.array([v.co[:] for v in h.data.vertices]);labels=np.array([next(h.vertex_groups[g.group].name[7:] for g in v.groups if h.vertex_groups[g.group].name.startswith('Region_')) for v in h.data.vertices])
def group_weights(n):
 idx=h.vertex_groups[n].index
 return np.array([sum(g.weight for g in v.groups if g.group==idx) for v in h.data.vertices])
sw=group_weights('Cloth_Scarf_Free');rw=group_weights('Cloth_Robe_Free');hw=group_weights('Cloth_Hood_Free')
# Only the neck attachment is pinned. Tall points on the distal scarf are free,
# too; a height mask would stretch a single connected tail against the neck.
tail=np.clip((.075-p[:,0]-.08)/.10,0,1)
sw=(labels=='Scarf')*tail*tail*(3-2*tail)
# Semantic islands already separate legs: the robe hem needs no lower-height pin.
upper=np.clip((p[:,2]-.38)/.10,0,1)
rw=(labels=='Robe')*(1-upper*upper*(3-2*upper))
# The source has an inward-facing underside near the polar axis, not only a shell.
# Fade cage influence there: angular coordinates are singular at the center.
radial=np.clip((np.linalg.norm(p[:,:2]-[.085,-.025],axis=1)-.02)/.06,0,1)
rw*=radial*radial*(3-2*radial)
# Remove only original triangles bridging the visibly open front slit; preserve vertices/UV.
bm=bmesh.new();bm.from_mesh(h.data);bridges=[];caps=[]
for face in bm.faces:
 q=np.array([v.co[:] for v in face.verts])
 ids=[v.index for v in face.verts]
 normal=np.cross(q[1]-q[0],q[2]-q[0]);normal/=max(np.linalg.norm(normal),1e-12);center=q.mean(0)
 if np.all(labels[ids]=='Robe') and center[2]<.27 and np.linalg.norm(center[:2]-[.085,-.025])<.13 and abs(normal[2])>.8:
  caps.append(face);continue
 crossings=[]
 for a,b in zip(q,np.roll(q,-1,axis=0)):
  if (a[0]-.085)*(b[0]-.085)<0:crossings.append(a+(b-a)*((.085-a[0])/(b[0]-a[0])))
 if np.all(labels[ids]=='Robe') and any(v[1]<-.025 and v[2]<.45 for v in crossings):bridges.append(face)
bmesh.ops.delete(bm,geom=bridges+caps,context='FACES_ONLY');bm.to_mesh(h.data);bm.free()
assert len(h.data.vertices)==len(p) and np.max(np.abs(p-np.array([v.co[:] for v in h.data.vertices])))<1e-7
nr,nt=10,37;nu,nv=19,9
robe=[];scarf=[];faces=[]
for i in range(nr):
 u=i/(nr-1)
 for j in range(nt):
  a=-math.pi/2+.14+(2*math.pi-.28)*j/(nt-1);robe.append((.085+(.10+.085*u)*math.cos(a),-.025+(.085+.065*u)*math.sin(a),.45-.25*u))
for i in range(nr-1):
 for j in range(nt-1):
  a=i*nt+j;faces.append((a,a+nt,a+nt+1,a+1))
for i in range(nu):
 u=i/(nu-1)
 for j in range(nv):
  v=2*j/(nv-1)-1;scarf.append((-.42*u,.12+.10*math.sin(u*math.pi),.57-.20*u+(.025+.10*u)*v))
robe=np.array(robe);scarf=np.array(scarf)
x,y,z=p.T;ru=np.clip((.45-z)/.25,0,1);angle=np.mod(np.arctan2((y+.025)/(.085+.065*ru),(x-.085)/(.10+.085*ru))+math.pi/2,2*math.pi)
rv=np.clip((angle-.14)/(2*math.pi-.28),0,1);su=np.clip(-x/.42,0,1);sv=np.clip(((z-(.57-.20*su))/(.025+.10*su)+1)/2,0,1)
ridx,rweights=grid_binding(ru,rv,nr,nt);sidx,sweights=grid_binding(su,sv,nu,nv)
def transform(points,bone):
 m=np.array(rig.matrix_world@rig.pose.bones[bone].matrix@rig.data.bones[bone].matrix_local.inverted())
 return points@m[:3,:3].T+m[:3,3]
def pos(n):return np.array(rig.matrix_world@rig.pose.bones[n].head)
def capsules():
 result=[]
 for a,b,r in [('Hips','Spine',.085),('Spine','Chest',.09),('Chest','Neck',.075),('Neck','Head',.06)]:result.append((pos(a),pos(b),r))
 for side in ['L','R']:
  for a,b,r in [('UpperArm','Forearm',.043),('Forearm','Hand',.043),('Thigh','Shin',.04),('Shin','Foot',.035),('Foot','Toe',.052)]:result.append((pos(a+'.'+side),pos(b+'.'+side),r))
 center=transform(np.array([[.065,0,.78]]),'Head')[0];result.append((center,center+np.array([0,0,.01]),.17))
 return result
s.frame_set(1);bpy.context.view_layer.update()
rs=Cloth(transform(robe,'Hips'),nr,nt,list(range(nt*3)),4)
ss=Cloth(transform(scarf,'Neck'),nu,nv,list(range(nv*3)),12)
positions=[];metrics=[];hoodtheta=0.;hoodvelocity=0.;lasthead=None;lastvelocity=np.zeros(3)
for step in range(60+90):
 f=max(1,step-59);s.frame_set(f);bpy.context.view_layer.update();deps=bpy.context.evaluated_depsgraph_get()
 base=np.array([tuple(rig.matrix_world@v.co) for v in h.evaluated_get(deps).data.vertices])
 rb=transform(robe,'Hips');sb=transform(scarf,'Neck');body=capsules()
 rn=rs.step(rb,body);tree=BVHTree.FromPolygons(rn.tolist(),faces,all_triangles=False)
 center=pos('Hips')
 def robe_contact(points,inv):
  for i in np.flatnonzero(inv):
   hit,normal,face,distance=tree.find_nearest(Vector(points[i]))
   if hit is None or distance>.06:continue
   hit=np.array(hit);normal=np.array(normal)
   if np.dot(normal[:2],hit[:2]-center[:2])<0:normal=-normal
   gap=float((points[i]-hit)@normal)
   if gap<.012:points[i]+=normal*(.012-gap)
  return points
 sn=ss.step(sb,body,robe_contact)
 q=base+((rn-rb)[ridx]*rweights[:,:,None]).sum(1)*rw[:,None]+((sn-sb)[sidx]*sweights[:,:,None]).sum(1)*sw[:,None]
 head=pos('Head');velocity=np.zeros(3) if lasthead is None else (head-lasthead)*30;acceleration=(velocity-lastvelocity)*30;lasthead=head;lastvelocity=velocity
 for _ in range(12):
  hoodvelocity+=(-2*acceleration[1]-150*hoodtheta-20*hoodvelocity-2000*hoodtheta**3)/360;hoodtheta+=hoodvelocity/360
 axis=np.array((rig.matrix_world@rig.pose.bones['Head'].matrix).to_3x3().col[0]);axis/=np.linalg.norm(axis)
 v=q-head;rot=v*math.cos(hoodtheta)+np.cross(axis,v)*math.sin(hoodtheta)+np.outer(v@axis,axis)*(1-math.cos(hoodtheta));q+=(rot-v)*hw[:,None]
 assert np.isfinite(q).all()
 if step>=60:
  positions.append(q.astype(np.float32));metrics.append({'frame':f,'hood_pitch_degrees':math.degrees(hoodtheta),'scarf_max_displacement':float(np.linalg.norm(q[sw>.5]-base[sw>.5],axis=1).max()),'robe_max_displacement':float(np.linalg.norm(q[rw>.5]-base[rw>.5],axis=1).max())})
 if step%15==0:print('PHYSICS',step,'of',150,flush=True)
# Save explicit world-space surface bake; original rigged motion stays in pixel-run.blend.
for mod in list(h.modifiers):h.modifiers.remove(mod)
h.parent=None;h.matrix_world.identity();h.shape_key_add(name='Tripo source surface')
for f,q in enumerate(positions,1):
 key=h.shape_key_add(name=f'Run cloth {f:03d}');key.data.foreach_set('co',q.ravel())
 for at,value in [(f-1,0),(f,1),(f+1,0)]:key.value=value;key.keyframe_insert('value',frame=at)
h['physics']='Independent world-space distance-constraint robe/scarf with gravity, drag, capsule and robe contacts; hood spring'
s.frame_set(1);bpy.ops.wm.save_as_mainfile(filepath=str(R/'outputs/pixel-run-cloth.blend'),compress=True)
np.savez_compressed(R/'outputs/pixel-run-cloth-cache.npz',positions=np.array(positions))
report={'frames':90,'settle_steps':60,'substeps_per_frame':8,'constraint_iterations':12,'cloth_nodes':len(robe)+len(scarf),'removed_front_slit_bridges':len(bridges),'removed_internal_bottom_cap_faces':len(caps),'gravity':9.81,'scarf_drag':12,'robe_drag':4,'body_collision':'moving bone capsules','garment_collision':'scarf nodes against simulated robe triangles','self_collision':False,'continuous_collision':False,'source':'outputs/pixel-run.blend','metrics':metrics,'status':'BAKED; validation recorded separately in pixel-run-cloth-validation.json'}
(R/'docs/logs/pixel-run-cloth.json').write_text(json.dumps(report,indent=2));print('CLOTH BAKE COMPLETE',flush=True)
for f in [10,25,40,55]:
 s.frame_set(f);s.render.filepath=str(R/f'outputs/pixel-run-cloth-pose-{f}.png');bpy.ops.render.render(write_still=True)

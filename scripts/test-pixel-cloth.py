"""Offline Blender cloth inertia test on independent cages driving Tripo skin.
T-pose translation is a test fixture, not a Kimodo or running animation.
"""
import bpy, math, json, os
import numpy as np
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
R=Path(__file__).resolve().parents[1]
OUT=R/'.cache/pixel-cloth'; OUT.mkdir(parents=True,exist_ok=True)
bpy.ops.wm.open_mainfile(filepath=str(R/'outputs/tripo-pixel-shaped.blend'))
scene=bpy.context.scene; scene.frame_start=1; scene.frame_end=150; scene.render.fps=30
hero=next(o for o in scene.objects if o.type=='MESH')
deps=bpy.context.evaluated_depsgraph_get()
newmesh=bpy.data.meshes.new_from_object(hero.evaluated_get(deps))
hero.shape_key_clear(); hero.data=newmesh
p=np.array([v.co[:] for v in hero.data.vertices]); colors=np.load(R/'outputs/tripo-pixel-inspection.npz')['colors']
assert len(colors)==len(p)
# The generated mesh contains bridges across the apparent front slit.
# Remove only triangles crossing its center line, keeping all vertex indices/UVs.
source=hero.data;keep=[];removed=0
for poly in source.polygons:
    q=p[list(poly.vertices)]
    bridge=(q[:,0].min()<0<q[:,0].max() and q[:,1].max()<-.06 and q[:,2].max()<.39 and q[:,2].min()>.215)
    if bridge:removed+=1
    else:keep.append(poly)
clean=bpy.data.meshes.new('Tripo skin with open robe slit')
clean.from_pydata(p.tolist(),[],[list(poly.vertices) for poly in keep]);clean.update()
for mat in source.materials:clean.materials.append(mat)
uv=clean.uv_layers.new(name=source.uv_layers.active.name)
for dst,src in zip(clean.polygons,keep):
    dst.use_smooth=src.use_smooth;dst.material_index=src.material_index
    for a,b in zip(dst.loop_indices,src.loop_indices):uv.data[a].uv=source.uv_layers.active.data[b].uv
hero.data=clean
print('Removed front-slit bridge triangles',removed,flush=True)
root=bpy.data.objects.new('Translation test fixture',None); scene.collection.objects.link(root)
hero.parent=root
for f,y in [(1,0),(30,0),(45,-.15),(75,-.9),(76,-.9),(105,-.9),(120,-.6),(135,0),(150,0)]:
    root.location.y=y; root.keyframe_insert('location',frame=f)
for fc in root.animation_data.action.fcurves:
    for k in fc.keyframe_points:k.interpolation='LINEAR'
root.location.y=0
def collider(name,loc,scale):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=16,ring_count=12,location=loc)
    ob=bpy.context.object; ob.name=name; ob.scale=scale
    bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
    ob.parent=root; ob.hide_render=True; ob.display_type='WIRE'
    ob.modifiers.new('Body collision','COLLISION'); ob.collision.thickness_outer=.004
    return ob
for name,loc,scale in [('head',(0,0,.79),(.15,.13,.17)),('torso',(0,0,.43),(.083,.065,.14)),('hips',(0,0,.29),(.085,.065,.055)),('legL',(-.065,0,.19),(.035,.04,.12)),('legR',(.065,0,.19),(.035,.04,.12)),('armL',(-.24,0,.52),(.16,.042,.042)),('armR',(.24,0,.52),(.16,.042,.042))]:collider(name,loc,scale)
def cage(name,verts,faces,pins,bend):
    m=bpy.data.meshes.new(name);m.from_pydata(verts,[],faces);m.update()
    ob=bpy.data.objects.new(name,m);scene.collection.objects.link(ob);ob.parent=root;ob.hide_render=True
    vg=ob.vertex_groups.new(name='Pinned attachment');vg.add(pins,1,'REPLACE')
    mod=ob.modifiers.new('Physical cloth','CLOTH');s=mod.settings
    s.quality=12;s.mass=.18;s.tension_stiffness=35;s.compression_stiffness=35;s.shear_stiffness=20;s.bending_stiffness=bend
    s.air_damping=3;s.vertex_group_mass=vg.name;s.pin_stiffness=1
    mod.collision_settings.use_collision=True;mod.collision_settings.distance_min=.004
    mod.collision_settings.collision_quality=6
    mod.collision_settings.use_self_collision=True
    mod.collision_settings.self_distance_min=.003
    mod.point_cache.frame_start=1;mod.point_cache.frame_end=150
    return ob,np.array(verts)
verts=[];oldverts=[];faces=[];nu=19;nv=9
for i in range(nu):
    u=i/(nu-1)
    for j in range(nv):
        v=j/(nv-1)*2-1
        oldverts.append((-.055-.37*u,.12+.075*math.sin(u*math.pi*.85)+.065*v*math.sin(u*math.pi),.57-.17*u+(.018+.10*u)*v))
        verts.append((-.055-.37*u,.15+.13*math.sin(u*math.pi*.85)+.065*v*math.sin(u*math.pi),.57-.17*u+(.018+.10*u)*v))
for i in range(nu-1):
    for j in range(nv-1):
        a=i*nv+j;faces.append((a,a+nv,a+nv+1,a+1))
scarf,scarfrest=cage('Scarf simulation surface',verts,faces,list(range(nv*4)),3)
scarfbase=np.array(oldverts)
verts=[];faces=[];nr=9;nt=37
for i in range(nr):
    u=i/(nr-1)
    for j in range(nt):
        a=-math.pi/2+.14+(2*math.pi-.28)*j/(nt-1)
        verts.append(((.091+.075*u)*math.cos(a),(.074+.041*u)*math.sin(a),.50-.245*u))
for i in range(nr-1):
    for j in range(nt-1):
        a=i*nt+j;faces.append((a,a+nt,a+nt+1,a+1))
robe,robebase=cage('Robe hem simulation surface',verts,faces,list(range(nt*3)),12)
# Scarf collides with the deformed robe, not just the smaller body ellipsoids.
robe.modifiers.new('Robe garment collision','COLLISION')
robe.collision.thickness_outer=.012
def smooth(a,b,v):
    t=np.clip((v-a)/(b-a),0,1);return t*t*(3-2*t)
x,y,z=p.T
teal=smooth(.08,.19,colors[:,2]-colors[:,0])*smooth(.15,.30,colors[:,1])
sw=teal*smooth(.055,.13,-x)*smooth(.0,.05,y)*smooth(.22,.29,z)*(1-smooth(.56,.61,z))
ru=np.clip((.50-z)/.245,0,1)
radius=np.sqrt((x/(.091+.075*ru))**2+(y/(.074+.041*ru))**2)
# The dark lining must follow the ivory shell. Texture brightness is NOT a pin mask.
robe_region=(radius>.60)&(radius<1.5)&(z>.215)&(z<.50)&(teal<.5)
rw=robe_region.astype(float)*(1-smooth(.40,.49,z))
def grid_binding(weight,u,v,rows,cols):
    ids=np.flatnonzero(weight>1e-6)
    a=np.clip(u[ids],0,1)*(rows-1);b=np.clip(v[ids],0,1)*(cols-1)
    i=np.minimum(a.astype(int),rows-2);j=np.minimum(b.astype(int),cols-2)
    a-=i;b-=j
    ix=np.stack([i*cols+j,(i+1)*cols+j,(i+1)*cols+j+1,i*cols+j+1],axis=1)
    w=np.stack([(1-a)*(1-b),a*(1-b),a*b,(1-a)*b],axis=1)
    return ids,ix,w,weight[ids]
angle=np.mod(np.arctan2(y/(.074+.041*ru),x/(.091+.075*ru))+math.pi/2,2*math.pi)
rv=np.clip((angle-.14)/(2*math.pi-.28),0,1)
su=np.clip((-x-.055)/.37,0,1)
sv=np.clip(((z-(.57-.17*su))/(.018+.10*su)+1)/2,0,1)
binds=[grid_binding(sw,su,sv,nu,nv),grid_binding(rw,ru,rv,nr,nt)]
hoodweight=smooth(.645,.73,z)*smooth(-.025,.10,y)
hoodtheta=0.;hoodvelocity=0.;previous_root_y=0.;previous_root_velocity=0.
hoodpivot=np.array([0,0,.65])
robe_faces=[]
for poly in hero.data.polygons:
    ids=list(poly.vertices);q=p[ids];c=q.mean(0)
    normal=np.cross(q[1]-q[0],q[2]-q[0])
    if .215<c[2]<.54 and teal[ids].mean()<.25 and np.dot(normal[:2],c[:2])>0 and .065<np.linalg.norm(c[:2])<.22:
        robe_faces.append(ids)
scarf_ids=np.flatnonzero(sw>.05)
_,dup=np.unique(np.round(p,6),axis=0,return_inverse=True);cnt=np.bincount(dup)
scene.render.resolution_x=scene.render.resolution_y=384;scene.cycles.samples=8
scene.render.film_transparent=False
cam=scene.camera;cam.parent=root;center=Vector((-.03,.03,.49))
cam.location=center+Vector((2.7,-1.6,0));cam.rotation_euler=(center-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.ortho_scale=1.3
hero.shape_key_add(name='Rest Tripo shape');key=hero.shape_key_add(name='Baked cloth');key.value=1
bpy.ops.wm.save_as_mainfile(filepath=str(R/'outputs/tripo-pixel-cloth-test.blend'),compress=True)
positions=[];metrics=[];caches=[[],[]]
reuse=np.load(R/'outputs/tripo-pixel-cloth-cache.npz') if os.environ.get('CLOTH_REUSE_CACHE') else None
if reuse is not None:raise RuntimeError('Recompute cloth: garment collision changed; old caches are not compatible')
if reuse is not None:
    for ob in [scarf,robe]:ob.modifiers['Physical cloth'].show_viewport=False
for f in range(1,151):
    scene.frame_set(f);deps=bpy.context.evaluated_depsgraph_get();delta=np.zeros_like(p)
    for k,(ob,base,bind) in enumerate(zip([scarf,robe],[scarfbase,robebase],binds)):
        if reuse is None:
            ev=ob.evaluated_get(deps);now=np.array([v.co[:] for v in ev.data.vertices])
        else:now=reuse[['scarf','robe'][k]][f-1]
        caches[k].append(now)
        ids,ix,w,weight=bind;delta[ids]+=((now-base)[ix]*w[:,:,None]).sum(1)*weight[:,None]
    avg=np.stack([np.bincount(dup,weights=delta[:,j])/cnt for j in range(3)],axis=1);delta=avg[dup]
    # Damped torsional spring driven by fixture acceleration, not a sine animation.
    root_y=float(root.location.y);velocity=(root_y-previous_root_y)*30
    acceleration=(velocity-previous_root_velocity)*30
    previous_root_y=root_y;previous_root_velocity=velocity
    for _ in range(12):
        hoodvelocity+=(5*acceleration-150*hoodtheta-18*hoodvelocity-2000*hoodtheta**3)/360
        hoodtheta+=hoodvelocity/360
    q=p-hoodpivot;rot=q.copy();cs=math.cos(hoodtheta);sn=math.sin(hoodtheta)
    rot[:,1]=q[:,1]*cs-q[:,2]*sn;rot[:,2]=q[:,1]*sn+q[:,2]*cs
    delta+=(rot-q)*hoodweight[:,None]
    coords=p+delta
    # Skin offsets can penetrate even when the coarse cloth surface collides.
    # Project the rendered scarf against the actual deformed outer robe surface.
    tree=BVHTree.FromPolygons(coords.tolist(),robe_faces,all_triangles=True)
    contact_count=0;max_correction=0.
    for vid in scarf_ids:
        if not .21<coords[vid,2]<.55:continue
        hit,normal,face,distance=tree.find_nearest(Vector(coords[vid]))
        if hit is None or distance>.10:continue
        normal=np.array(normal);hit=np.array(hit)
        if np.dot(normal[:2],hit[:2])<0:normal=-normal
        gap=float(np.dot(coords[vid]-hit,normal))
        if gap<.006:
            correction=(.006-gap)*normal
            coords[vid]+=correction;contact_count+=1
            max_correction=max(max_correction,float(np.linalg.norm(correction)))
    assert np.isfinite(coords).all()
    key.data.foreach_set('co',coords.astype(np.float32).ravel())
    positions.append(coords.astype(np.float32))
    metrics.append({'frame':f,'scarf_tip':caches[0][-1][-nv:].mean(0).tolist(),'robe_hem':caches[1][-1][-nt:].mean(0).tolist(),'max_skin_displacement':float(np.linalg.norm(coords-p,axis=1).max()),'hood_pitch_degrees':math.degrees(hoodtheta),'hood_tip_displacement':float(np.linalg.norm((rot-q)[np.argmax(y*(z>.7))])),'scarf_robe_contacts':contact_count,'max_scarf_skin_contact_correction':max_correction})
    if f>=31 and (not os.environ.get('CLOTH_SAMPLE_ONLY') or f in [31,75,90,125]):
        scene.render.filepath=str(OUT/f'{f-30:03d}.png');bpy.ops.render.render(write_still=True)
    print('CLOTH_FRAME',f,flush=True)
if os.environ.get('CLOTH_SAMPLE_ONLY'):
    print('SAMPLE INSPECTION COMPLETE',flush=True)
    raise SystemExit(0)
np.savez_compressed(R/'outputs/tripo-pixel-cloth-cache.npz',scarf=np.array(caches[0]),robe=np.array(caches[1]))
key.value=0
for f,coords in enumerate(positions,1):
    bk=hero.shape_key_add(name=f'Physical bake {f:03d}')
    bk.data.foreach_set('co',coords.ravel())
    for at,value in [(f-1,0),(f,1),(f+1,0)]:
        bk.value=value;bk.keyframe_insert('value',frame=at)
for ob in [scarf,robe]:
    ob.modifiers['Physical cloth'].show_viewport=False
    ob.modifiers['Physical cloth'].show_render=False
scene.frame_set(31)
bpy.ops.wm.save_as_mainfile(filepath=str(R/'outputs/tripo-pixel-cloth-test.blend'),compress=True)
(R/'docs/logs/tripo-pixel-cloth.json').write_text(json.dumps({'test':'T-pose world translation, start/stop/reverse; NOT running animation','physics':'Blender cloth, independent surfaces with pinned roots, body ellipsoid collisions; deformed robe garment collider','hood_physics':'Acceleration-driven torsional spring, 12 substeps/frame, front aperture fixed; not full cloth simulation','hood_spring':{'acceleration_coupling':5,'stiffness':150,'damping':18,'cubic_stiffness':2000},'scarf_skin_contact':'6mm unilateral projection against rendered outer robe, supplements coarse cloth collisions','frames':150,'fps':30,'settle_frames':30,'cloth_quality':12,'self_collision':True,'render_skin':'Parametric bilinear binding, separate front slit banks; dark robe lining follows shell','removed_front_slit_bridge_triangles':removed,'simulation_cache_reused':reuse is not None,'scarf_attachment':'4 pinned rows, 0.03m posterior offset, broader root bend','production_ready':False,'metrics':metrics},indent=2))

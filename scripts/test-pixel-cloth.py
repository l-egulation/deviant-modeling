"""Offline Blender cloth inertia test on independent cages driving Tripo skin.
T-pose translation is a test fixture, not a Kimodo or running animation.
"""
import bpy, math, json
import numpy as np
from pathlib import Path
from mathutils import Vector
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
verts=[];faces=[];nu=19;nv=9
for i in range(nu):
    u=i/(nu-1)
    for j in range(nv):
        v=j/(nv-1)*2-1
        verts.append((-.055-.37*u,.12+.075*math.sin(u*math.pi*.85)+.065*v*math.sin(u*math.pi),.57-.17*u+(.018+.10*u)*v))
for i in range(nu-1):
    for j in range(nv-1):
        a=i*nv+j;faces.append((a,a+nv,a+nv+1,a+1))
scarf,scarfbase=cage('Scarf simulation surface',verts,faces,list(range(nv*2)),.8)
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
def smooth(a,b,v):
    t=np.clip((v-a)/(b-a),0,1);return t*t*(3-2*t)
x,y,z=p.T
teal=smooth(.08,.19,colors[:,2]-colors[:,0])*smooth(.15,.30,colors[:,1])
sw=teal*smooth(.055,.13,-x)*smooth(.0,.05,y)*smooth(.22,.29,z)*(1-smooth(.56,.61,z))
rw=(1-teal)*smooth(.45,.65,colors[:,0])*(1-smooth(.40,.49,z))*smooth(.18,.21,z)
def binding(base,weight):
    ids=np.flatnonzero(weight>1e-6);dist=((p[ids,None,:]-base[None,:,:])**2).sum(2)
    ix=np.argsort(dist,axis=1)[:,:4];w=1/np.maximum(np.take_along_axis(dist,ix,axis=1),1e-6);w/=w.sum(1)[:,None]
    return ids,ix,w,weight[ids]
binds=[binding(scarfbase,sw),binding(robebase,rw)]
_,dup=np.unique(np.round(p,6),axis=0,return_inverse=True);cnt=np.bincount(dup)
scene.render.resolution_x=scene.render.resolution_y=384;scene.cycles.samples=8
scene.render.film_transparent=False
cam=scene.camera;cam.parent=root;center=Vector((-.03,.03,.49))
cam.location=center+Vector((2.7,-1.6,0));cam.rotation_euler=(center-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.ortho_scale=1.3
hero.shape_key_add(name='Rest Tripo shape');key=hero.shape_key_add(name='Baked cloth');key.value=1
bpy.ops.wm.save_as_mainfile(filepath=str(R/'outputs/tripo-pixel-cloth-test.blend'),compress=True)
positions=[];metrics=[];caches=[[],[]]
for f in range(1,151):
    scene.frame_set(f);deps=bpy.context.evaluated_depsgraph_get();delta=np.zeros_like(p)
    for k,(ob,base,bind) in enumerate(zip([scarf,robe],[scarfbase,robebase],binds)):
        ev=ob.evaluated_get(deps);now=np.array([v.co[:] for v in ev.data.vertices]);caches[k].append(now)
        ids,ix,w,weight=bind;delta[ids]+=((now-base)[ix]*w[:,:,None]).sum(1)*weight[:,None]
    avg=np.stack([np.bincount(dup,weights=delta[:,j])/cnt for j in range(3)],axis=1);delta=avg[dup]
    coords=p+delta
    assert np.isfinite(coords).all()
    key.data.foreach_set('co',coords.astype(np.float32).ravel())
    positions.append(coords.astype(np.float32))
    metrics.append({'frame':f,'scarf_tip':caches[0][-1][-nv:].mean(0).tolist(),'robe_hem':caches[1][-1][-nt:].mean(0).tolist(),'max_skin_displacement':float(np.linalg.norm(delta,axis=1).max())})
    if f>=31:
        scene.render.filepath=str(OUT/f'{f-30:03d}.png');bpy.ops.render.render(write_still=True)
    print('CLOTH_FRAME',f,flush=True)
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
(R/'docs/logs/tripo-pixel-cloth.json').write_text(json.dumps({'test':'T-pose world translation, start/stop/reverse; NOT running animation','physics':'Blender cloth, independent surfaces with pinned roots, body ellipsoid collisions','frames':150,'fps':30,'settle_frames':30,'cloth_quality':12,'self_collision':True,'render_skin':'4-neighbour inverse-distance cage displacement; topology preserved','production_ready':False,'metrics':metrics},indent=2))

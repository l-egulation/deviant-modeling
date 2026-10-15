"""Build an editable T-arm / spread-leg deformation model from the hero design.

Keeps the original textured rigid accessories; constructs a new quad coat,
continuous sleeve roots and new joint-loop trousers. Never edits the source GLB.
"""
import bpy,bmesh,json,math,sys
import numpy as np
from pathlib import Path
from mathutils import Vector,Matrix,Quaternion
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'outputs'
(ROOT/'.cache').mkdir(exist_ok=True)
bpy.ops.wm.open_mainfile(filepath=str(OUT/'hero-run.blend'))
source=bpy.data.objects['InkHero'];oldrig=bpy.data.objects['HeroRig']
source_data=source.data.copy();source_materials=list(source.data.materials)
coords=np.array([v.co[:] for v in source_data.vertices])
# Texture labels only select rigid design details, never determine deform weights.
shader=next(n for n in source_materials[0].node_tree.nodes if n.type=='BSDF_PRINCIPLED')
texture=shader.inputs['Base Color'].links[0].from_node.image
width,height=texture.size;pixels=np.empty(width*height*4,dtype=np.float32);texture.pixels.foreach_get(pixels);pixels=pixels.reshape(height,width,4)
rgb=np.zeros((len(coords),3));uv=source_data.uv_layers.active.data
for poly in source_data.polygons:
    for li in poly.loop_indices:
        v=source_data.loops[li].vertex_index;u=uv[li].uv;rgb[v]=pixels[int(u.y*height)%height,int(u.x*width)%width,:3]
blue=(rgb[:,2]>rgb[:,0]*1.2)&(rgb[:,1]>rgb[:,0]*1.2)&(rgb[:,2]>.05)
head_mask=(coords[:,2]>.565)|(blue&(coords[:,2]>.52))|((np.abs(coords[:,0])<.034)&(coords[:,1]<-.11)&(coords[:,2]>.54)&(coords[:,2]<.635))
for obj in list(bpy.data.objects):bpy.data.objects.remove(obj,do_unlink=True)
for action in list(bpy.data.actions):bpy.data.actions.remove(action)
s=bpy.context.scene;s.frame_start=1;s.frame_end=120;s.render.fps=30;s.render.fps_base=1
parts=[];weight_records={}

def smooth(x,a,b):
    t=min(1,max(0,(x-a)/(b-a)));return t*t*(3-2*t)

def material(name,color):
    m=bpy.data.materials.new(name);m.diffuse_color=(*color,1);m.use_nodes=True
    p=m.node_tree.nodes.get('Principled BSDF');p.inputs['Base Color'].default_value=(*color,1);p.inputs['Roughness'].default_value=.78
    return m

ivory=material('Hero_Coat_Ivory',(.78,.745,.64));trim=material('Hero_Seam_Ivory',(.61,.575,.49));pantsmat=material('Hero_Trousers',(.72,.69,.61))

def make_mesh(name,vertices,faces,weights,mat):
    used=sorted({i for face in faces for i in face});remap={old:new for new,old in enumerate(used)}
    vertices=[vertices[i] for i in used];weights=[weights[i] for i in used];faces=[tuple(remap[i] for i in face) for face in faces]
    mesh=bpy.data.meshes.new(name);mesh.from_pydata(vertices,[],faces);mesh.update()
    obj=bpy.data.objects.new(name,mesh);bpy.context.collection.objects.link(obj);mesh.materials.append(mat)
    for p in mesh.polygons:p.use_smooth=True
    parts.append(obj);weight_records[name]=weights
    return obj

def extract(name,mask,bone,transform=None):
    mesh=source_data.copy();obj=bpy.data.objects.new(name,mesh);bpy.context.collection.objects.link(obj)
    bm=bmesh.new();bm.from_mesh(mesh);bm.verts.ensure_lookup_table()
    bmesh.ops.delete(bm,geom=[v for v in bm.verts if not mask[v.index]],context='VERTS')
    if transform is not None:
        for v in bm.verts:v.co=transform @ v.co
    bm.to_mesh(mesh);bm.free();mesh.update()
    obj.vertex_groups.clear()
    for p in mesh.polygons:p.use_smooth=True
    parts.append(obj);weight_records[name]=[{bone:1} for v in mesh.vertices]
    return obj

extract('Hero_HoodFaceScarf',head_mask,'Head')
for side,sign in (('Left',1),('Right',-1)):
    # Keep the stylized original gloves, but rotate them into the new bind pose.
    mask=(coords[:,0]*sign>.198)&(coords[:,2]>.22)&(coords[:,2]<.39)&(rgb.max(1)<.42)
    old=Vector((sign*.263,.005,.349));new=Vector((sign*.375,.01,.50))
    q=Vector((sign*.012,0,-.046)).normalized().rotation_difference(Vector((sign,0,0)))
    transform=Matrix.Translation(new) @ q.to_matrix().to_4x4() @ Matrix.Translation(-old)
    extract('Hero_'+side+'Glove',mask,side+'Hand',transform)
    gold=(rgb[:,0]>rgb[:,2]*1.5)&(rgb[:,1]>rgb[:,2]*1.15)&(rgb[:,0]>.15)
    mask=(coords[:,0]*sign>0)&(coords[:,2]<.155)&((coords[:,2]<.108)|gold)
    extract('Hero_'+side+'Boot',mask,side+'Foot',Matrix.Translation((sign*(.185-.137),0,0)))

# Quad torso with actual side armholes. Each hole shares its boundary vertices
# with the sleeve, so there is no separate floating sleeve at the shoulder.
N=32;zs=(.34,.35,.37,.40,.43,.46,.49,.52,.55,.565)
rx=(.145,.15,.15,.145,.14,.14,.145,.15,.145,.115)
ry=(.096,.10,.103,.103,.102,.10,.098,.092,.080,.065)
verts=[];faces=[];weights=[]
def body_weights(co):
    x,y,z=co;upper=smooth(z,.385,.49);side='Left' if x>0 else 'Right'
    shoulder=smooth(abs(x),.065,.135)*smooth(z,.425,.49)*(1-smooth(z,.55,.575))
    return {'Spine1':1-upper,'Chest':upper*(1-.8*shoulder),side+'Clavicle':upper*.25*shoulder,side+'Arm':upper*.55*shoulder}
for j,z in enumerate(zs):
    for k in range(N):
        a=2*math.pi*k/N;co=(rx[j]*math.cos(a),.01+ry[j]*math.sin(a),z);verts.append(co);weights.append(body_weights(co))
removed=[]
for j in range(len(zs)-1):
    for k in range(N):
        face=(j*N+k,j*N+(k+1)%N,(j+1)*N+(k+1)%N,(j+1)*N+k)
        if 4<=j<8 and (k in (29,30,31,0,1,2) or 13<=k<19):removed.append(face)
        else:faces.append(face)

for side,sign,allowed in (('Left',1,set((29,30,31,0,1,2))),('Right',-1,set(range(13,19)))):
    patch=[face for face in removed if face[0]%N in allowed]
    edge_counts={}
    for face in patch:
        for a,b in zip(face,face[1:]+face[:1]):
            pair=tuple(sorted((a,b)));edge_counts[pair]=edge_counts.get(pair,0)+1
    adjacency={}
    for (a,b),count in edge_counts.items():
        if count==1:adjacency.setdefault(a,[]).append(b);adjacency.setdefault(b,[]).append(a)
    boundary=[min(adjacency)];last=None
    while True:
        options=[i for i in adjacency[boundary[-1]] if i!=last]
        nxt=next((i for i in options if i not in boundary),None)
        if nxt is None:break
        last=boundary[-1];boundary.append(nxt)
    assert len(boundary)==20,len(boundary)
    angles=np.unwrap([math.atan2(verts[i][2]-.49,verts[i][1]-.01) for i in boundary])
    previous=boundary
    for x,radius in ((.17,.059),(.195,.058),(.225,.057),(.25,.057),(.265,.059),(.275,.059),(.29,.056),(.315,.052),(.345,.050),(.365,.050),(.375,.051)):
        ring=[]
        for a in angles:
            co=(sign*x,.01+radius*math.cos(a),.50+radius*math.sin(a));ring.append(len(verts));verts.append(co)
            clav=(1-smooth(x,.15,.22))*.4;fore=smooth(x,.205,.34);hand=smooth(x,.345,.39)*.3
            weights.append({side+'Clavicle':clav,side+'Arm':(1-clav)*(1-fore),side+'ForeArm':(1-clav)*fore*(1-hand),side+'Hand':(1-clav)*fore*hand})
        for k in range(20):faces.append((previous[k],previous[(k+1)%20],ring[(k+1)%20],ring[k]))
        previous=ring
coat=make_mesh('Hero_Coat',verts,faces,weights,ivory)

def tube(name,centers,radii,side,kind,mat,sides=20):
    vertices=[];faces=[];records=[]
    direction=(Vector(centers[-1])-Vector(centers[0])).normalized()
    u=Vector((0,1,0));v=direction.cross(u).normalized()
    for j,(center,radius) in enumerate(zip(centers,radii)):
        center=Vector(center);ring_v=v
        if kind=='leg':
            # Bring the trouser hem onto the level boot cuff. A perpendicular
            # cut on the spread leg leaves an exposed wedge above the boot.
            blend=smooth(j/(len(centers)-1),.78,1)
            sign=1 if side=='Left' else -1
            ring_v=(v*(1-blend)+Vector((1,0,0))*blend).normalized()
            center.x=center.x*(1-blend)+sign*.185*blend
        for k in range(sides):
            a=2*math.pi*k/sides;co=center+radius*(math.cos(a)*u+math.sin(a)*ring_v);vertices.append(co[:])
            if kind=='leg':
                # Physical distance, not ring number: closely spaced knee
                # support loops must not concentrate the skin transition.
                thigh=smooth(center[2],.125,.32);hip=smooth(center[2],.31,.335)*.4
                records.append({'Hips':hip,side+'UpLeg':(1-hip)*thigh,side+'Leg':(1-hip)*(1-thigh)})
            else:records.append({side+'ForeArm':.8,side+'Hand':.2})
        if j:
            for k in range(sides):faces.append(((j-1)*sides+k,(j-1)*sides+(k+1)%sides,j*sides+(k+1)%sides,j*sides+k))
    return make_mesh(name,vertices,faces,records,mat)

for side,sign in (('Left',1),('Right',-1)):
    centers=[]
    for z in (.335,.32,.30,.275,.245,.23,.22,.21,.195,.175,.155,.135):
        t=(.345-z)/.245;centers.append((sign*(.08+.105*t),.015,z))
    tube('Hero_'+side+'Trouser',centers,(.074,.075,.075,.073,.071,.069,.068,.068,.066,.063,.060,.057),side,'leg',pantsmat)
    tube('Hero_'+side+'Cuff',[(sign*.355,.01,.50),(sign*.36,.01,.50),(sign*.374,.01,.50),(sign*.379,.01,.50)],(.052,.055,.055,.052),side,'cuff',ivory)

def detail(name,location,scale,mat,bone='Chest'):
    bpy.ops.mesh.primitive_cube_add(size=1,location=location);o=bpy.context.object;o.name=name;o.scale=scale
    bpy.ops.object.transform_apply(location=True,rotation=True,scale=True)
    bevel=o.modifiers.new('Rounded seam','BEVEL');bevel.width=.003;bevel.segments=3;bpy.context.view_layer.objects.active=o;bpy.ops.object.modifier_apply(modifier=bevel.name)
    o.data.materials.append(mat)
    for p in o.data.polygons:p.use_smooth=True
    parts.append(o);weight_records[name]=[body_weights(v.co) for v in o.data.vertices]
    return o
detail('Hero_Zipper',(0,-.096,.442),(.004,.005,.176),trim)
for sign in (-1,1):detail('Hero_Pocket_'+str(sign),(sign*.072,-.085,.408),(.035,.008,.064),ivory)

spec={'Hips':((0,.015,.34),(0,.015,.405),None),'Spine1':((0,.015,.405),(0,.012,.475),'Hips'),'Chest':((0,.012,.475),(0,.01,.555),'Spine1'),'Head':((0,.01,.555),(0,.01,.92),'Chest')}
for side,sign in (('Left',1),('Right',-1)):
    spec.update({side+'Clavicle':((sign*.035,.01,.51),(sign*.135,.01,.50),'Chest'),side+'Arm':((sign*.135,.01,.50),(sign*.27,.01,.50),side+'Clavicle'),side+'ForeArm':((sign*.27,.01,.50),(sign*.375,.01,.50),side+'Arm'),side+'Hand':((sign*.375,.01,.50),(sign*.423,.01,.50),side+'ForeArm'),side+'UpLeg':((sign*.08,.015,.345),(sign*.1325,.015,.2225),'Hips'),side+'Leg':((sign*.1325,.015,.2225),(sign*.185,.02,.10),side+'UpLeg'),side+'Foot':((sign*.185,.02,.10),(sign*.185,-.10,.052),side+'Leg')})
data=bpy.data.armatures.new('HeroModelRig');rig=bpy.data.objects.new('HeroModelRig',data);bpy.context.collection.objects.link(rig);bpy.context.view_layer.objects.active=rig;rig.select_set(True);bpy.ops.object.mode_set(mode='EDIT')
for name,(head,tail,parent) in spec.items():
    b=data.edit_bones.new(name);b.head=head;b.tail=tail
    if parent:b.parent=data.edit_bones[parent]
bpy.ops.object.mode_set(mode='OBJECT');rig.show_in_front=True
for b in rig.pose.bones:b.rotation_mode='QUATERNION'
for obj in parts:
    for name in spec:obj.vertex_groups.new(name=name)
    for i,record in enumerate(weight_records[obj.name]):
        total=sum(record.values())
        for name,w in record.items():
            if w>1e-8:obj.vertex_groups[name].add([i],w/total,'REPLACE')
    if obj.name=='Hero_Coat' or 'Trouser' in obj.name or 'Cuff' in obj.name:
        # Normals follow the continuous sleeve junction before subdivision.
        bm=bmesh.new();bm.from_mesh(obj.data);bmesh.ops.recalc_face_normals(bm,faces=bm.faces);bm.to_mesh(obj.data);bm.free()
        sub=obj.modifiers.new('Joint surface subdivision','SUBSURF');sub.levels=sub.render_levels=1
        shell=obj.modifiers.new('Cloth edge thickness','SOLIDIFY');shell.thickness=.0025;shell.offset=-1
    mod=obj.modifiers.new('Mapped skeleton','ARMATURE');mod.object=rig;obj.parent=rig

# Pose tests start from the wide bind pose, with independent shoulder controls.
for frame in range(1,121):
    t=(frame-1)/119;wave=math.sin(math.pi*t)**2
    for b in rig.pose.bones:
        angle=0;axis=Vector((0,1,0))
        if b.name.endswith('Clavicle'):axis=Vector((0,0,1));angle=math.radians(12)*math.sin(2*math.pi*t)
        if b.name.endswith('Arm') and not b.name.endswith('ForeArm'):angle=math.radians(65)*wave*(1 if b.name.startswith('Left') else -1)
        if b.name.endswith('ForeArm'):axis=Vector((0,0,1));angle=math.radians(65)*wave
        if b.name.endswith('Leg') and not b.name.endswith('UpLeg'):axis=Vector((1,0,0));angle=math.radians(55)*wave
        # Convert intended global-rest-axis rotation into this bone's axes.
        basis=b.bone.matrix_local.to_3x3();local_axis=basis.inverted() @ axis
        b.rotation_quaternion=Quaternion(local_axis,angle);b.keyframe_insert('rotation_quaternion',frame=frame)
rig.animation_data.action.name='HeroModel_JointTest_4s';s.frame_set(1)
rig['bind_pose']='Horizontal T arms; spread legs about 23 degrees; front -Y, up Z'
rig['source_design']='assets/ink-hero.glb; rigid hood/face/scarf, gloves and boots retained'
rig['body_rebuilt']=True

bpy.ops.object.camera_add(location=(1.65,-3.3,1.0));camera=bpy.context.object;camera.name='HeroModelCamera';camera.data.type='ORTHO';camera.data.ortho_scale=1.18;camera.rotation_euler=(Vector((0,0,.49))-camera.location).to_track_quat('-Z','Y').to_euler();s.camera=camera
for pos,energy,size in (((1,-2,3),350,3),((-2,-1,2),220,3),((0,2,2),250,2)):
    bpy.ops.object.light_add(type='AREA',location=pos);o=bpy.context.object;o.data.energy=energy;o.data.shape='DISK';o.data.size=size;o.rotation_euler=(Vector((0,0,.5))-o.location).to_track_quat('-Z','Y').to_euler()
s.world.color=(.2,.2,.2);s.render.engine='CYCLES';s.cycles.samples=24;s.cycles.use_denoising=True
prefs=bpy.context.preferences.addons['cycles'].preferences;prefs.compute_device_type='CUDA';prefs.get_devices()
for d in prefs.devices:d.use=d.type=='CUDA'
s.cycles.device='GPU';s.render.resolution_x=s.render.resolution_y=640;s.render.resolution_percentage=100;s.view_settings.view_transform='Standard';s.view_settings.exposure=-.7;s.render.image_settings.file_format='PNG';s.render.film_transparent=False
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'hero-model.blend'),compress=True)
bpy.ops.object.select_all(action='DESELECT')
for o in parts:o.select_set(True)
rig.select_set(True);bpy.context.view_layer.objects.active=rig
bpy.ops.export_scene.gltf(filepath=str(OUT/'hero-model.glb'),use_selection=True,export_apply=True,export_animations=True,export_frame_range=True,export_force_sampling=True,export_animation_mode='SCENE')
report={'status':'BUILT_REQUIRES_DEFORMATION_REVIEW','source':'assets/ink-hero.glb via existing raw working mesh','rig_bones':len(spec),'parts':{o.name:{'vertices':len(o.data.vertices),'quads':sum(len(p.vertices)==4 for p in o.data.polygons),'faces':len(o.data.polygons)} for o in parts},'new_deform_geometry':['Hero_Coat','Hero_LeftTrouser','Hero_RightTrouser'],'coat_connected_sleeve_boundary_vertices_per_side':20,'bind_pose':rig['bind_pose'],'clip':'Independent joint test, not Kimodo run','clip_frames':120,'fps':30}
(ROOT/'docs/logs/hero-model-build.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
for name,pos in (('front',(0,-3,.49)),('side',(-3,0,.49)),('three-quarter',(1.65,-3.3,1.0))):
    s.frame_set(1);camera.location=pos;camera.rotation_euler=(Vector((0,0,.49))-camera.location).to_track_quat('-Z','Y').to_euler();s.render.filepath=str(ROOT/f'.cache/hero-model-{name}.png');bpy.ops.render.render(write_still=True)

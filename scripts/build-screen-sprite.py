"""Camera-specific shape study on a COPY of the approved baked animation.
Corrective geometry follows existing bones. This is not a fresh cloth simulation.
"""
import bpy,math,json,colorsys,os
import numpy as np
from pathlib import Path
from mathutils import Vector,Matrix
R=Path(__file__).resolve().parents[1];O=R/'outputs/pixel-screen-study';O.mkdir(exist_ok=True)
bpy.ops.wm.open_mainfile(filepath=str(R/'outputs/pixel-run-cloth.blend'))
s=bpy.context.scene;obj=bpy.data.objects['TripoPixel_Character'];rig=bpy.data.objects['TripoPixel_Rig'];cam=s.camera
cam.animation_data_clear();cam.data.type='ORTHO';cam.data.ortho_scale=1.36
offset=Vector((math.cos(math.radians(45)),-math.sin(math.radians(45)),0))*3
cam.rotation_euler=(-offset).to_track_quat('-Z','Y').to_euler()
s.render.film_transparent=True;s.render.image_settings.file_format='PNG';s.render.image_settings.color_mode='RGBA'
s.render.resolution_x=s.render.resolution_y=384;s.render.resolution_percentage=100
s.render.engine='CYCLES';s.cycles.samples=8;s.cycles.device='CPU'
s.view_settings.view_transform='Standard';s.view_settings.look='None';s.view_settings.exposure=0;s.view_settings.gamma=1
img=next(n.image for n in obj.data.materials[0].node_tree.nodes if n.type=='TEX_IMAGE' and n.image)
w,h=img.size;pix=np.array(img.pixels[:],dtype=np.float32).reshape(h,w,4);uv=obj.data.uv_layers.active.data
labels=[]
for poly in obj.data.polygons:
 samples=[]
 for li in poly.loop_indices:
  u,v=uv[li].uv;samples.append(pix[int(v*h)%h,int(u*w)%w,:3])
 r,g,b=np.median(samples,axis=0);hue,sat,val=colorsys.rgb_to_hsv(float(r),float(g),float(b))
 labels.append(3 if b>r*1.12 and g>r*1.1 else (2 if val<.20 else (5 if r>g*1.22 and g>b*1.35 and sat>.5 else 0)))
palette=['FDEEDA','D2B396','1B1616','025673','02648C','EBA516']
def linear(x):return x/12.92 if x<=.04045 else ((x+.055)/1.055)**2.4
obj.data.materials.clear()
for c in palette:
 m=bpy.data.materials.new('Screen_'+c);m.use_nodes=True;n=m.node_tree.nodes;n.clear();l=m.node_tree.links
 out=n.new('ShaderNodeOutputMaterial');em=n.new('ShaderNodeEmission')
 em.inputs['Color'].default_value=tuple(linear(int(c[i:i+2],16)/255) for i in (0,2,4))+(1,)
 l.new(em.outputs[0],out.inputs['Surface']);obj.data.materials.append(m)
keys=obj.data.shape_keys.key_blocks;p=np.array([v.co[:] for v in keys[0].data]);x,y,z=p.T
regions=np.array([next(obj.vertex_groups[g.group].name[7:] for g in v.groups if obj.vertex_groups[g.group].name.startswith('Region_')) for v in obj.data.vertices])
for poly,label in zip(obj.data.polygons,labels):
 c=p[list(poly.vertices)].mean(0);region=regions[poly.vertices[0]]
 if label==0 and ((region=='Hood' and c[1]>.065 and c[2]<.82) or(region=='Robe' and c[0]<.035)):label=1
 if label==3 and region=='Scarf' and c[2]>.535 and c[0]>-.05:label=4
 poly.material_index=label
def smooth(a,b,v):
 t=np.clip((v-a)/(b-a),0,1);return t*t*(3-2*t)
hood=(regions=='Hood')*smooth(.63,.72,z)
edited=p.copy()
# Lower the conical crown and pull its tip toward the back of the head.
top=smooth(.78,.96,z)*hood
edited[:,2]-=.105*top;edited[:,1]+=.155*top
rear=smooth(.04,.15,y)*smooth(.73,.86,z)*hood
edited[:,1]+=.10*rear;edited[:,2]-=.065*rear
edited[:,0]=.065+(edited[:,0]-.065)*(1+.10*hood)
# Present the face toward the fixed game camera, fading to zero at the neck.
rotation=np.array(Matrix.Rotation(math.radians(22),3,'Z'));center=np.array([.065,-.02,.73])
turned=(edited-center)@rotation.T+center
edited+=(turned-edited)*hood[:,None]
delta=edited-p
# Free tail only: extend rearward, broaden its vertical sheet, keep collar fixed.
tail=(regions=='Scarf')*smooth(.06,.30,.075-x)
scarf_delta=np.zeros_like(p);scarf_delta[:,1]=.20*tail
scarf_delta[:,2]=(z-.47)*.18*tail
# Reduce the cylindrical sleeve depth without changing hands or joints.
sleeve=np.isin(regions,['Robe','Arm.L','Arm.R'])*smooth(.12,.22,np.abs(x-.075))*(1-smooth(.27,.34,np.abs(x-.075)))*smooth(.40,.46,z)*(1-smooth(.54,.58,z))
sleeve_delta=np.zeros_like(p);sleeve_delta[:,1]=-(y+.025)*.30*sleeve
weights={}
for bone in rig.data.bones:
 if bone.use_deform:
  idx=obj.vertex_groups[bone.name].index
  weights[bone.name]=np.array([sum(g.weight for g in v.groups if g.group==idx) for v in obj.data.vertices])
base={f:np.array([v.co[:] for v in keys[f'Run cloth {f:03d}'].data]) for f in range(1,91)}
def displacement(f):
 s.frame_set(f);bpy.context.view_layer.update()
 def rot(name):return np.array((rig.matrix_world@rig.pose.bones[name].matrix@rig.data.bones[name].matrix_local.inverted()).to_3x3())
 d=delta@rot('Head').T+scarf_delta@rot('Neck').T
 for name,weight in weights.items():d+=(sleeve_delta@rot(name).T)*weight[:,None]
 return d
deltas={f:displacement(f) for f in range(1,91)}
assert all(np.isfinite(d).all() for d in deltas.values())
# Two simple eye marks attached to the existing face, oriented to the fixed
# capture camera. Original irregular gold texture is hidden only in the study.
gold_faces=[poly for poly,label in zip(obj.data.polygons,labels) if label==5 and all(regions[v]=='Hood' for v in poly.vertices)]
gold_ids=np.unique([i for poly in gold_faces for i in poly.vertices]);assert len(gold_ids)>2
median=np.median(p[gold_ids,0]);eye_groups=[gold_ids[p[gold_ids,0]<median],gold_ids[p[gold_ids,0]>=median]]
right=np.array(cam.rotation_euler.to_matrix()@Vector((1,0,0)));up=np.array([0,0,1]);toward=np.array(offset.normalized())
eyes=[]
for index,ids in enumerate(eye_groups):
 mesh=bpy.data.meshes.new(f'Graphic eye {index}');mesh.from_pydata([tuple(right*x+up*z) for x,z in [(-.009,-.023),(.009,-.023),(.009,.023),(-.009,.023)]],[],[(0,1,2,3)])
 eye=bpy.data.objects.new(f'Graphic eye {index}',mesh);s.collection.objects.link(eye);mesh.materials.append(obj.data.materials[5]);eyes.append(eye)
 for f in range(1,91):
  face_center=(base[f][gold_ids]+deltas[f][gold_ids]).mean(0)
  eye.location=Vector(face_center+right*((index-.5)*.046)+toward*.035);eye.keyframe_insert('location',frame=f)
frames=[49] if os.environ.get('SCREEN_QUICK')=='1' else list(range(45,67))
for mode in ['before','after']:
 for eye in eyes:eye.hide_render=(mode=='before')
 for poly in gold_faces:poly.material_index=5 if mode=='before' else 2
 folder=O/mode;folder.mkdir(exist_ok=True)
 for f in range(1,91):keys[f'Run cloth {f:03d}'].data.foreach_set('co',(base[f]+(deltas[f] if mode=='after' else 0)).ravel())
 for f in frames:
  s.frame_set(f);cam.location=Vector((.075+rig.location.x,rig.location.y,.51))+offset;bpy.context.view_layer.update()
  s.render.filepath=str(folder/f'{f-45:03d}.png');bpy.ops.render.render(write_still=True)
# Save camera tracking for normal playback in the derived scene.
for f in [1,90]:
 s.frame_set(f);cam.location=Vector((.075+rig.location.x,rig.location.y,.51))+offset;cam.keyframe_insert('location',frame=f)
for layer in cam.animation_data.action.layers:
 for strip in layer.strips:
  for bag in strip.channelbags:
   for curve in bag.fcurves:
    for key in curve.keyframe_points:key.interpolation='LINEAR'
s.frame_set(49)
if os.environ.get('SCREEN_QUICK')!='1':bpy.ops.wm.save_as_mainfile(filepath=str(O/'screen-character.blend'),compress=True)
(O/'study.json').write_text(json.dumps({'source':'outputs/pixel-run-cloth.blend','frames':frames,'palette':palette,'camera_degrees_from_side':45,'canvas':128,'output_mirrored_to_face_right':True,'shape_changes':['lower rearward hood tip','head presentation with neck fade','rearward broader scarf tail','reduced sleeve depth'],'max_corrective_displacement_m':max(float(np.linalg.norm(d,axis=1).max()) for d in deltas.values()),'bone_motion_changed':False,'cloth_resimulated':False,'collision_verified':False,'loop_verified':False},indent=2))

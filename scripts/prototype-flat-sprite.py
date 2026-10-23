"""One-pose art-direction study: constant colors and fixed rest-space shadow patches."""
import bpy,math,json,colorsys
import numpy as np
from pathlib import Path
from mathutils import Vector
R=Path(__file__).resolve().parents[1];O=R/'outputs/pixel-flat-study';O.mkdir(exist_ok=True)
bpy.ops.wm.open_mainfile(filepath=str(R/'outputs/pixel-run-cloth.blend'))
s=bpy.context.scene;obj=bpy.data.objects['TripoPixel_Character'];rig=bpy.data.objects['TripoPixel_Rig'];cam=s.camera
s.frame_set(49);cam.animation_data_clear();cam.data.type='ORTHO';cam.data.ortho_scale=1.36
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
 m=bpy.data.materials.new('Flat_'+c);m.use_nodes=True;n=m.node_tree.nodes;n.clear();l=m.node_tree.links
 out=n.new('ShaderNodeOutputMaterial');em=n.new('ShaderNodeEmission')
 em.inputs['Color'].default_value=tuple(linear(int(c[i:i+2],16)/255) for i in (0,2,4))+(1,)
 l.new(em.outputs[0],out.inputs['Surface']);obj.data.materials.append(m)
rest=np.array([v.co[:] for v in obj.data.shape_keys.key_blocks[0].data])
regions=[next(obj.vertex_groups[g.group].name[7:] for g in v.groups if obj.vertex_groups[g.group].name.startswith('Region_')) for v in obj.data.vertices]
for mode in ['flat','patch']:
 for poly,label in zip(obj.data.polygons,labels):
  c=rest[list(poly.vertices)].mean(0);x,y,z=c;region=regions[poly.vertices[0]]
  # Broad painted areas bound to the original mesh, not tiny posed normals.
  if mode=='patch':
   if label==0 and ((region=='Hood' and y>.065 and z<.82) or (region=='Robe' and x<.035)):label=1
   if label==3 and region=='Scarf' and z>.535 and x>-.05:label=4
  poly.material_index=label
 for angle in [30,45,60]:
  offset=Vector((math.cos(math.radians(angle)),-math.sin(math.radians(angle)),0))*3
  cam.rotation_euler=(-offset).to_track_quat('-Z','Y').to_euler();cam.location=Vector((.075+rig.location.x,rig.location.y,.51))+offset
  bpy.context.view_layer.update();s.render.filepath=str(O/f'{mode}-{angle}.png');bpy.ops.render.render(write_still=True)
(O/'study.json').write_text(json.dumps({'source':'outputs/pixel-run-cloth.blend','source_frame':49,'angles':[30,45,60],'palette':palette,'modes':['constant flat colors','fixed broad rest-space patches'],'geometry_or_animation_changed':False,'full_animation_verified':False},indent=2))

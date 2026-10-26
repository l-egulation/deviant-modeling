"""Capture approved run with immutable six-color materials and a shared pivot."""
import bpy,math,json,colorsys,os
import numpy as np
from pathlib import Path
from mathutils import Vector
R=Path(__file__).resolve().parents[1];tag=os.environ.get('MOTION_TAG','pixel-run');O=R/f'outputs/{tag}-sprites'
capture_frames=list(range(1,91)) if tag=='pixel-idle' else list(range(45,67))
for name in ['original','render']:(O/name).mkdir(parents=True,exist_ok=True)
bpy.ops.wm.open_mainfile(filepath=str(R/f'outputs/{tag}-cloth.blend'))
s=bpy.context.scene;obj=bpy.data.objects['TripoPixel_Character'];rig=bpy.data.objects['TripoPixel_Rig'];cam=s.camera
cam.animation_data_clear();cam.data.type='ORTHO';cam.data.ortho_scale=1.36
# Keep a fixed 30-degree front-side view, matching the accepted run preview.
angle=60 if tag=='pixel-idle' else 30
offset=Vector((math.cos(math.radians(angle)),-math.sin(math.radians(angle)),0))*3
cam.rotation_euler=(-offset).to_track_quat('-Z','Y').to_euler()
s.render.fps=30;s.render.film_transparent=True
s.render.image_settings.file_format='PNG';s.render.image_settings.color_mode='RGBA'
s.render.resolution_percentage=100;s.render.engine='CYCLES';s.cycles.samples=8;s.cycles.device='CPU'
s.view_settings.view_transform='Standard';s.view_settings.look='None';s.view_settings.exposure=0;s.view_settings.gamma=1
def frame(f):
 s.frame_set(f);cam.location=Vector((.075+rig.location.x,rig.location.y,.51))+offset;bpy.context.view_layer.update()
def render(folder,index,size):
 s.render.resolution_x=s.render.resolution_y=size
 s.render.filepath=str(O/f'{folder}/{index:03d}.png');bpy.ops.render.render(write_still=True)
for i,f in enumerate(capture_frames):
 frame(f);render('original',i,384)
img=next(n.image for n in obj.data.materials[0].node_tree.nodes if n.type=='TEX_IMAGE' and n.image)
w,h=img.size;pix=np.array(img.pixels[:],dtype=np.float32).reshape(h,w,4);uv=obj.data.uv_layers.active.data
palette=['FDEEDA','D2B396','1B1616','025673','02648C','EBA516']
def linear(x):return x/12.92 if x<=.04045 else ((x+.055)/1.055)**2.4
materials=[]
for name,base,shadow in [('Ivory',0,1),('Dark',2,2),('Teal',4,3),('Gold',5,5)]:
 m=bpy.data.materials.new('Sprite_'+name);m.use_nodes=True;n=m.node_tree.nodes;n.clear();l=m.node_tree.links
 out=n.new('ShaderNodeOutputMaterial');em=n.new('ShaderNodeEmission');l.new(em.outputs[0],out.inputs['Surface'])
 ramp=n.new('ShaderNodeValToRGB');ramp.color_ramp.interpolation='CONSTANT'
 for e,idx,pos in zip(ramp.color_ramp.elements,[shadow,base],[0,.18]):
  e.position=pos;e.color=tuple(linear(int(palette[idx][i:i+2],16)/255) for i in (0,2,4))+(1,)
 # A threshold rather than gradients; broad lit areas, selective shadows.
 geo=n.new('ShaderNodeNewGeometry');dot=n.new('ShaderNodeVectorMath');dot.operation='DOT_PRODUCT';dot.inputs[1].default_value=(.35,-.55,.76)
 l.new(geo.outputs['Normal'],dot.inputs[0]);l.new(dot.outputs['Value'],ramp.inputs[0]);l.new(ramp.outputs['Color'],em.inputs[0]);materials.append(m)
labels=[]
for poly in obj.data.polygons:
 samples=[]
 for li in poly.loop_indices:
  u,v=uv[li].uv;samples.append(pix[int(v*h)%h,int(u*w)%w,:3])
 r,g,b=np.median(samples,axis=0);hue,sat,val=colorsys.rgb_to_hsv(float(r),float(g),float(b))
 labels.append(2 if b>r*1.12 and g>r*1.1 else (1 if val<.20 else (3 if r>g*1.22 and g>b*1.35 and sat>.5 else 0)))
obj.data.materials.clear()
for m in materials:obj.data.materials.append(m)
for p,label in zip(obj.data.polygons,labels):p.material_index=label
for i,f in enumerate(capture_frames):
 frame(f);render('render',i,384)
# Same phase on the next cycle: quantify cloth drift separately from body timing.
keys=obj.data.shape_keys.key_blocks
def local(f):
 s.frame_set(f);return np.array([v.co[:] for v in keys[f'Run cloth {f:03d}'].data])-np.array(rig.location)
drift=np.linalg.norm(local(67)-local(45),axis=1)
meta={'source':'outputs/pixel-run-cloth.blend','motion':'Mixamo Running With Intention on fitted rig + independent cloth','source_frames':list(range(45,67)),'fps':30,'frame_count':22,'duration_seconds':22/30,'canvas':[128,128],'palette':palette,'camera':'orthographic 30 degrees from side; fixed height; root XY tracking','ground_pivot':[64,112],'per_frame_crop':False,'texture':'UV-sampled region classification only; texture discarded from output shading','same_phase_cloth_drift_m':{'max':float(drift.max()),'p95':float(np.quantile(drift,.95))},'loop_seam_verified':False}
if tag=='pixel-idle':
 meta.update({'source':f'outputs/{tag}-cloth.blend','motion':'authored breathing idle on original fitted rig; newly simulated cloth; not generated or mocap','source_frames':capture_frames,'frame_count':90,'duration_seconds':3,'same_phase_cloth_drift_m':None,'camera':'orthographic 60 degrees from side (30 from front); fixed height and scale'})
(O/'capture.json').write_text(json.dumps(meta,indent=2))
print(json.dumps(meta),flush=True)

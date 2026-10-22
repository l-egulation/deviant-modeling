import bpy, math, json, colorsys
import numpy as np
from pathlib import Path
from mathutils import Vector
R=Path(__file__).resolve().parents[1]; O=R/'outputs/art-style-prototype'; O.mkdir(exist_ok=True)
bpy.ops.wm.open_mainfile(filepath=str(R/'outputs/hero-mixamo-run.blend'))
s=bpy.context.scene; obj=bpy.data.objects['TripoHero']; rig=bpy.data.objects['TripoRunRig']; cam=s.camera
s.frame_set(6); cam.animation_data_clear(); s.render.film_transparent=True
s.render.resolution_x=s.render.resolution_y=384;s.render.resolution_percentage=100
s.render.image_settings.file_format='PNG';s.render.image_settings.color_mode='RGBA'
s.render.engine='CYCLES';s.cycles.samples=8;s.cycles.device='CPU'
s.view_settings.view_transform='Standard';s.view_settings.look='None';s.view_settings.exposure=0;s.view_settings.gamma=1
cam.data.type='ORTHO';cam.data.ortho_scale=1.5
# Identical root-relative ground anchor and scale at each angle.
def camera(angle):
 a=math.radians(angle); offset=Vector((math.cos(a),-math.sin(a),math.tan(math.radians(5))))*3
 cam.rotation_euler=(-offset).to_track_quat('-Z','Y').to_euler()
 cam.location=Vector((rig.location.x,rig.location.y,0))+offset+cam.rotation_euler.to_matrix()@Vector((0,.5,0))
 bpy.context.view_layer.update()
def render(name):
 s.render.filepath=str(O/(name+'.png'));bpy.ops.render.render(write_still=True)
camera(30);render('original-30')
# Classify original UV texture into material regions, then discard texture detail.
img=next(n.image for n in obj.data.materials[0].node_tree.nodes if n.type=='TEX_IMAGE' and n.image)
w,h=img.size; pix=np.array(img.pixels[:],dtype=np.float32).reshape(h,w,4)
uv=obj.data.uv_layers.active.data
palette=['FDEEDA','D2B396','1B1616','025673','02648C','EBA516']
def linear(x):return x/12.92 if x<=.04045 else ((x+.055)/1.055)**2.4
materials=[]
for name,base,shadow in [('Ivory',0,1),('Dark',2,2),('Teal',4,3),('Gold',5,5)]:
 m=bpy.data.materials.new('Art_'+name);m.use_nodes=True;n=m.node_tree.nodes;n.clear();l=m.node_tree.links
 out=n.new('ShaderNodeOutputMaterial');em=n.new('ShaderNodeEmission');l.new(em.outputs[0],out.inputs['Surface'])
 ramp=n.new('ShaderNodeValToRGB');ramp.color_ramp.interpolation='CONSTANT'
 for e,idx,pos in zip(ramp.color_ramp.elements,[shadow,base],[0,.30]):
  e.position=pos;e.color=tuple(linear(int(palette[idx][i:i+2],16)/255) for i in (0,2,4))+(1,)
 geo=n.new('ShaderNodeNewGeometry');dot=n.new('ShaderNodeVectorMath');dot.operation='DOT_PRODUCT';dot.inputs[1].default_value=(-.3,-.6,.74)
 l.new(geo.outputs['Normal'],dot.inputs[0]);l.new(dot.outputs['Value'],ramp.inputs[0]);l.new(ramp.outputs['Color'],em.inputs[0]);materials.append(m)
labels=[]
for p in obj.data.polygons:
 samples=[]
 for li in p.loop_indices:
  u,v=uv[li].uv;samples.append(pix[min(h-1,int(v*h)%h),min(w-1,int(u*w)%w),:3])
 r,g,b=np.median(samples,axis=0); hue,sat,val=colorsys.rgb_to_hsv(float(r),float(g),float(b))
 label=2 if b>r*1.12 and g>r*1.1 else (1 if val<.20 else (3 if r>g*1.22 and g>b*1.35 and sat>.5 else 0))
 labels.append(label)
obj.data.materials.clear()
for m in materials:obj.data.materials.append(m)
for p,label in zip(obj.data.polygons,labels):p.material_index=label
for angle in [0,30,45]:camera(angle);render('flat-'+str(angle))
camera(30);bpy.ops.wm.save_as_mainfile(filepath=str(O/'prototype.blend'))
(O/'render-settings.json').write_text(json.dumps({'source':'outputs/hero-mixamo-run.blend','frame':6,'angles':[0,30,45],'palette':palette,'material_assignment':'UV texture sampled per polygon; provisional semantic classification','geometry_modified':False,'cloth_implemented':False,'ortho_scale':1.5,'ground_pivot_at_96':[48,80]},indent=2))

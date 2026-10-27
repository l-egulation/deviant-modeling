"""Compare shading only on unchanged baked geometry. No generative editing.

Store a smoothed rest-surface lighting field as a POINT attribute. The field is
attached to vertex identities, so cloth/skin deformation cannot repaint it.
"""
import bpy, math, json, hashlib, os, sys
import numpy as np
from pathlib import Path
from mathutils import Vector

R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'scripts'))
from pixel_shadow_design import authored_shadow, RULES
designed=os.environ.get('DESIGNED_SHADOWS')=='1'
config=json.loads(Path(os.environ['STYLE_CONFIG']).read_text()) if os.environ.get('STYLE_CONFIG') else {}
O=R/('outputs/pixel-painted-style' if designed else 'outputs/pixel-surface-style')
if config: O=R/config['output']
O.mkdir(parents=True,exist_ok=True)
palette=['FDEEDA','D2B396','1B1616','025673','02648C','EBA516']
modes=['fixed','designed'] if designed else ['dynamic','fixed','hybrid'];report={}
if config: modes=config.get('modes',modes)
def digest(mesh):
 h=hashlib.sha256()
 for key in mesh.shape_keys.key_blocks:
  a=np.empty(len(mesh.vertices)*3,dtype=np.float32);key.data.foreach_get('co',a);h.update(a.tobytes())
 return h.hexdigest()
def linear(v):return v/12.92 if v<=.04045 else ((v+.055)/1.055)**2.4

clips=[('pixel-idle',list(range(1,91))),('pixel-run',list(range(45,67)))] if designed else [('pixel-idle',list(range(1,91,3))),('pixel-run',[45,49,55])]
if config: clips=[(c['tag'],c['frames']) for c in config['clips']]
for tag,frames in clips:
 settings=next((c for c in config.get('clips',[]) if c['tag']==tag),{})
 input_path=settings.get('input',f'outputs/{tag}-cloth.blend')
 bpy.ops.wm.open_mainfile(filepath=str(R/input_path))
 s=bpy.context.scene;obj=bpy.data.objects['TripoPixel_Character'];rig=bpy.data.objects['TripoPixel_Rig'];mesh=obj.data
 before=digest(mesh)
 image=next(n.image for n in mesh.materials[0].node_tree.nodes if n.type=='TEX_IMAGE' and n.image)
 w,h=image.size;pixels=np.array(image.pixels[:],dtype=np.float32).reshape(h,w,4);uv=mesh.uv_layers.active.data
 labels=[]
 for p in mesh.polygons:
  rgb=np.median([pixels[int(uv[i].uv.y*h)%h,int(uv[i].uv.x*w)%w,:3] for i in p.loop_indices],axis=0)
  r,g,b=rgb;val=max(rgb);sat=(val-min(rgb))/max(val,1e-8)
  labels.append(2 if b>r*1.12 and g>r*1.1 else (1 if val<.20 else (3 if r>g*1.22 and g>b*1.35 and sat>.5 else 0)))
 if config.get('clean_parts'):
  from pixel_local_repair import clean_materials
  labels=clean_materials(obj,labels)
 # Normals from the undeformed Basis, identical artistic reference across clips.
 # Mesh normals correspond to Basis coordinates, not animated evaluated mesh.
 normals=np.array([v.normal[:] for v in mesh.vertices],dtype=np.float64)
 edges=np.array([e.vertices[:] for e in mesh.edges],dtype=int)
 for _ in range(30):
  total=normals.copy();count=np.ones(len(normals))
  np.add.at(total,edges[:,0],normals[edges[:,1]]);np.add.at(total,edges[:,1],normals[edges[:,0]])
  np.add.at(count,edges[:,0],1);np.add.at(count,edges[:,1],1)
  normals=total/count[:,None];normals/=np.maximum(np.linalg.norm(normals,axis=1)[:,None],1e-8)
 field=normals@np.array([.35,-.55,.76])
 attr=mesh.attributes.new('StyleRestLight','FLOAT','POINT');attr.data.foreach_set('value',field.astype(np.float32))
 fieldhash=hashlib.sha256(field.astype(np.float32).tobytes()).hexdigest()
 if designed:
  paint,counts=authored_shadow(obj,readable=config.get('readable_shadows',False))
  attr=mesh.attributes.new('StyleDesignedLight','FLOAT','POINT');attr.data.foreach_set('value',paint)
 camera=s.camera;camera.animation_data_clear();camera.data.type='ORTHO';camera.data.ortho_scale=1.96
 angle=math.radians(settings.get('angle',60))
 offset=Vector((math.cos(angle),-math.sin(angle),0))*3;camera.rotation_euler=(-offset).to_track_quat('-Z','Y').to_euler()
 s.render.engine='CYCLES';s.cycles.samples=4;s.cycles.use_denoising=False;s.cycles.seed=0;s.cycles.use_animated_seed=False
 s.render.resolution_x=s.render.resolution_y=384;s.render.resolution_percentage=100
 s.render.film_transparent=True;s.render.image_settings.file_format='PNG';s.render.image_settings.color_mode='RGBA'
 s.view_settings.view_transform='Standard';s.view_settings.look='None';s.view_settings.exposure=0;s.view_settings.gamma=1
 for mode in modes:
  mesh.materials.clear()
  for name,base,shadow in [('Ivory',0,1),('Dark',2,2),('Teal',4,3),('Gold',5,5)]:
   m=bpy.data.materials.new('SurfaceStyle_'+mode+'_'+name);m.use_nodes=True;n=m.node_tree.nodes;n.clear();links=m.node_tree.links
   out=n.new('ShaderNodeOutputMaterial');em=n.new('ShaderNodeEmission');links.new(em.outputs[0],out.inputs['Surface'])
   ramp=n.new('ShaderNodeValToRGB');ramp.color_ramp.interpolation='CONSTANT'
   for e,index,pos in zip(ramp.color_ramp.elements,[shadow,base],[0,.18]):
    e.position=pos;e.color=tuple(linear(int(palette[index][i:i+2],16)/255) for i in (0,2,4))+(1,)
   geo=n.new('ShaderNodeNewGeometry');dot=n.new('ShaderNodeVectorMath');dot.operation='DOT_PRODUCT';dot.inputs[1].default_value=(.35,-.55,.76);links.new(geo.outputs['Normal'],dot.inputs[0])
   rest=n.new('ShaderNodeAttribute');rest.attribute_name='StyleDesignedLight' if mode=='designed' else 'StyleRestLight'
   if mode=='dynamic':links.new(dot.outputs['Value'],ramp.inputs[0])
   elif mode in ['fixed','designed']:links.new(rest.outputs['Fac'],ramp.inputs[0])
   else:
    fixed=n.new('ShaderNodeMath');fixed.operation='MULTIPLY';fixed.inputs[1].default_value=.85;links.new(rest.outputs['Fac'],fixed.inputs[0])
    live=n.new('ShaderNodeMath');live.operation='MULTIPLY';live.inputs[1].default_value=.15;links.new(dot.outputs['Value'],live.inputs[0])
    add=n.new('ShaderNodeMath');add.operation='ADD';links.new(fixed.outputs[0],add.inputs[0]);links.new(live.outputs[0],add.inputs[1]);links.new(add.outputs[0],ramp.inputs[0])
   links.new(ramp.outputs['Color'],em.inputs[0]);mesh.materials.append(m)
  for p,label in zip(mesh.polygons,labels):p.material_index=label
  directory=O/'raw'/tag/mode;directory.mkdir(parents=True,exist_ok=True)
  for f in frames:
   s.frame_set(f);camera.location=Vector((.075+rig.location.x,rig.location.y,.6125))+offset;bpy.context.view_layer.update()
   s.render.filepath=str(directory/f'{f:03d}.png');bpy.ops.render.render(write_still=True)
  print('COMPLETE',tag,mode,flush=True)
 after=digest(mesh);assert before==after
 report[tag]={'input':input_path,'angle':math.degrees(angle),'frames':frames,'geometry_shape_key_sha256_before':before,'geometry_shape_key_sha256_after':after,'fixed_field_sha256':fieldhash,'fixed_field_range':[float(field.min()),float(field.max())]}
 if designed:report[tag].update({'designed_field_sha256':hashlib.sha256(paint.tobytes()).hexdigest(),'shadow_vertices_by_region':counts})
report.update({'palette':palette,'modes':modes,'idle_sampling_fps':10,'idle_duration_s':3,'camera_degrees_from_side':60,'ortho_scale':1.96,'ground_y':104,'canvas':[128,128],'shadows':'30 iterations of adjacency-smoothed Basis normals stored on vertices; hybrid85%fixed15%live','limitations':['procedural shadow prototype, not hand-painted UV artwork','fixed shadow follows surface but can look painted at other angles','no geometry or motion edits, no AI images','sampling10fps does not establish 30fps stability']})
if designed:
 report.update({'idle_sampling_fps':30,'shadows':RULES,'limitations':['designed parametric masks, not hand-painted UV texture','source geometry/motion preserved','loop seam not guaranteed']})
 if not config: assert report['pixel-idle']['designed_field_sha256']==report['pixel-run']['designed_field_sha256']
if config:
 report['configuration']=config
 report['camera_degrees_from_side']='per-clip angle'
 report['shadows']=dict(RULES,hood='side wedge x > .23 + .12*(z-.65)' if config.get('readable_shadows') else RULES['hood'])
 report['limitations']=['geometry preserved during rendering; idle pose and cloth may differ from prior study','no AI images or per-frame cleanup','loop seam not guaranteed']
(O/'render-validation.json').write_text(json.dumps(report,indent=2))

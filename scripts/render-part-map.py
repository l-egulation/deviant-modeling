"""Render persistent semantic face IDs from the original mesh, no geometry edits."""
import bpy, colorsys, hashlib, json, math
from pathlib import Path
import numpy as np
from mathutils import Vector
R=Path(__file__).resolve().parents[1];O=R/'outputs/pixel-part-style';O.mkdir(parents=True,exist_ok=True)
names=['background','hood','face','eye.L','eye.R','scarf.collar','clasp','robe','sleeve.L','sleeve.R','glove.L','glove.R','leg.L','leg.R','boot.L','boot.R','cuff.L','cuff.R','scarf.tail']
colors=[[0,0,0]]+[[round(c*255) for c in colorsys.hsv_to_rgb((i*.61803398875)%1,.75,1)] for i in range(1,len(names))]
report={'names':names,'colors':colors,'camera':75,'resolution':384,'clips':{}}
def linear(v): return v/12.92 if v<=.04045 else ((v+.055)/1.055)**2.4
def digest(mesh):
 h=hashlib.sha256()
 for key in mesh.shape_keys.key_blocks:
  a=np.empty(len(mesh.vertices)*3,dtype=np.float32);key.data.foreach_get('co',a);h.update(a.tobytes())
 return h.hexdigest()
for tag,source,frames in [('idle','pixel-readable-idle',range(1,91)),('run','pixel-run',range(45,67))]:
 bpy.ops.wm.open_mainfile(filepath=str(R/f'outputs/{source}-cloth.blend'))
 s=bpy.context.scene;obj=bpy.data.objects['TripoPixel_Character'];rig=bpy.data.objects['TripoPixel_Rig'];mesh=obj.data;before=digest(mesh)
 image=next(n.image for n in mesh.materials[0].node_tree.nodes if n.type=='TEX_IMAGE' and n.image)
 w,h=image.size;pixels=np.array(image.pixels[:]).reshape(h,w,4);uv=mesh.uv_layers.active.data
 regions=[next(obj.vertex_groups[g.group].name[7:] for g in v.groups if obj.vertex_groups[g.group].name.startswith('Region_')) for v in mesh.vertices]
 ids=[]
 for p in mesh.polygons:
  region=max(set(regions[v] for v in p.vertices),key=lambda r:sum(regions[v]==r for v in p.vertices))
  x,y,z=np.mean([mesh.vertices[v].co[:] for v in p.vertices],axis=0)
  r,g,b=np.median([pixels[int(uv[i].uv.y*h)%h,int(uv[i].uv.x*w)%w,:3] for i in p.loop_indices],axis=0)
  teal=b>r*1.12 and g>r*1.1;dark=max(r,g,b)<.20;gold=not teal and r>g*1.22 and g>b*1.35 and (max(r,g,b)-min(r,g,b))/max(max(r,g,b),1e-8)>.5
  side=0 if region.endswith('.L') else 1
  if region=='Hood': identity=(3 if x>.075 else 4) if gold else (2 if dark else 1)
  elif teal or region=='Scarf': identity=6 if gold else (18 if x<-.005 else 5)
  elif region.startswith('Arm.'): identity=(10 if dark else 8)+side
  elif region.startswith('Leg.'): identity=(16 if gold else (14 if z<.105 else 12))+side
  else: identity=6 if gold else 7
  ids.append(identity)
 mesh.materials.clear()
 for name,color in zip(names,colors):
  m=bpy.data.materials.new('Part_'+name);m.use_nodes=True;n=m.node_tree.nodes;n.clear();l=m.node_tree.links
  out=n.new('ShaderNodeOutputMaterial');em=n.new('ShaderNodeEmission');em.inputs[0].default_value=tuple(linear(c/255) for c in color)+(1,);l.new(em.outputs[0],out.inputs['Surface']);mesh.materials.append(m)
 for p,i in zip(mesh.polygons,ids):p.material_index=i
 cam=s.camera;cam.animation_data_clear();cam.data.type='ORTHO';cam.data.ortho_scale=1.96;angle=math.radians(75);offset=Vector((math.cos(angle),-math.sin(angle),0))*3;cam.rotation_euler=(-offset).to_track_quat('-Z','Y').to_euler()
 s.render.engine='CYCLES';s.cycles.samples=4;s.cycles.use_denoising=False;s.cycles.seed=0;s.cycles.use_animated_seed=False
 s.render.resolution_x=s.render.resolution_y=384;s.render.resolution_percentage=100;s.render.film_transparent=True
 s.render.image_settings.file_format='PNG';s.render.image_settings.color_mode='RGBA';s.view_settings.view_transform='Standard';s.view_settings.look='None';s.view_settings.exposure=0;s.view_settings.gamma=1
 dest=O/'raw'/tag;dest.mkdir(parents=True,exist_ok=True)
 for f in frames:
  s.frame_set(f);cam.location=Vector((.075+rig.location.x,rig.location.y,.6125))+offset;bpy.context.view_layer.update();s.render.filepath=str(dest/f'{f:03d}.png');bpy.ops.render.render(write_still=True)
 assert digest(mesh)==before
 report['clips'][tag]={'frames':list(frames),'source':source,'geometry_hash_unchanged':before,'face_counts':{n:ids.count(i) for i,n in enumerate(names)}}
(O/'part-map.json').write_text(json.dumps(report,indent=2));print('PART MAP COMPLETE',flush=True)

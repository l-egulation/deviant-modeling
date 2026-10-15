"""Render a front diagnostic overlay of the new bind joints, without saving it."""
import bpy,math
from pathlib import Path
from mathutils import Vector
ROOT=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(ROOT/'outputs/hero-model.blend'))
s=bpy.context.scene;s.frame_set(1);r=bpy.data.objects['HeroModelRig'];c=s.camera
c.location=(0,-3,.49);c.rotation_euler=Vector((0,1,0)).to_track_quat('-Z','Y').to_euler();c.data.ortho_scale=1.18
mat=bpy.data.materials.new('JointGuide');mat.use_nodes=True
nodes=mat.node_tree.nodes;nodes.clear();em=nodes.new('ShaderNodeEmission');em.inputs['Color'].default_value=(.02,.75,1,1);em.inputs['Strength'].default_value=1.5;out=nodes.new('ShaderNodeOutputMaterial');mat.node_tree.links.new(em.outputs[0],out.inputs['Surface'])
for b in r.data.bones:
    a=Vector((b.head_local.x,-.30,b.head_local.z));end=Vector((b.tail_local.x,-.30,b.tail_local.z));delta=end-a
    bpy.ops.mesh.primitive_cylinder_add(vertices=12,radius=.002,depth=max(.002,delta.length),location=(a+end)/2)
    o=bpy.context.object;o.rotation_euler=delta.to_track_quat('Z','Y').to_euler();o.data.materials.append(mat)
    bpy.ops.mesh.primitive_uv_sphere_add(segments=12,ring_count=8,radius=.006,location=a);bpy.context.object.data.materials.append(mat)
s.render.resolution_x=s.render.resolution_y=640;s.cycles.samples=16
prefs=bpy.context.preferences.addons['cycles'].preferences;prefs.compute_device_type='CUDA';prefs.get_devices()
for d in prefs.devices:d.use=d.type=='CUDA'
s.cycles.device='GPU';s.render.filepath=str(ROOT/'outputs/hero-model-rig.png');bpy.ops.render.render(write_still=True)
print('RIG_OVERLAY_RENDERED: projected bind joints; diagnostic guides not saved into model')

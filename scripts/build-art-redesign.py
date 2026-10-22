"""Partial redesign of the actual Tripo A mesh; static art gate before motion/cloth."""
import bpy, math, json
from pathlib import Path
from mathutils import Vector,Matrix
R=Path(__file__).resolve().parents[1];O=R/'outputs/hero-art-redesign';O.mkdir(exist_ok=True)
bpy.ops.wm.open_mainfile(filepath=str(R/'outputs/art-style-prototype/prototype.blend'))
s=bpy.context.scene;hero=bpy.data.objects['TripoHero'];rig=bpy.data.objects['TripoRunRig'];cam=s.camera
rig.animation_data_clear();rig.location=(0,0,0);rig.rotation_euler=(0,0,0)
for pb in rig.pose.bones:pb.matrix_basis=Matrix.Identity(4)
s.frame_set(1)
original=[v.co.copy() for v in hero.data.vertices]
# Keep limb proportions; reshape only hood, widen front face aperture with its surrounding vertices.
for v in hero.data.vertices:
 x,y,z=v.co
 if z>.64:
  front=max(0,min(1,(-y-.015)/.13));vertical=max(0,1-abs(z-.79)/.18)
  v.co.x*=1+.13*front*vertical
  rear=max(0,min(1,(y+.01)/.16));upper=max(0,1-abs(z-.89)/.16)
  v.co.y+=.15*rear*upper
  v.co.z+=.025*rear*upper
# Remove tiny original jacket texture masks; assign clear garment regions without changing limbs.
for p in hero.data.polygons:
 z=sum(original[i].z for i in p.vertices)/len(p.vertices);x=sum(abs(original[i].x) for i in p.vertices)/len(p.vertices)
 if .31<z<.60 and x<.35:p.material_index=0
# Broad front-lit regions; keep discrete palette, reduce excess shadows.
for name in ['Art_Ivory','Art_Teal']:
 m=bpy.data.materials[name]
 for n in m.node_tree.nodes:
  if n.type=='VECT_MATH':n.inputs[1].default_value=(.35,-.8,.48)
  if n.type=='VALTORGB':n.color_ramp.elements[1].position=.05
mats=[bpy.data.materials['Art_'+n] for n in ['Ivory','Dark','Teal','Gold']]
def mesh(name,verts,faces,material,bone):
 me=bpy.data.meshes.new(name);me.from_pydata(verts,[],faces);me.update();ob=bpy.data.objects.new(name,me);s.collection.objects.link(ob);me.materials.append(mats[material]);ob.parent=rig
 vg=ob.vertex_groups.new(name=bone);vg.add(list(range(len(verts))),1,'REPLACE');mod=ob.modifiers.new('Rig attachment','ARMATURE');mod.object=rig
 return ob
# Open-front short robe shell: widening lower hem, actual separated front edges.
verts=[];faces=[];N=32
for k,(z,rx,ry) in enumerate([(.49,.115,.102),(.40,.122,.105),(.28,.175,.145)]):
 for j in range(N+1):
  a=.13+(2*math.pi-.26)*j/N
  verts.append((rx*math.sin(a),-ry*math.cos(a)+.012,z))
for k in range(2):
 for j in range(N):
  a=k*(N+1)+j;faces.append((a,a+1,a+N+2,a+N+1))
robe=mesh('ArtRobe',verts,faces,0,'Hips')
# Blend upper attachment to torso; hem stays independent of legs for later cloth work.
robe.vertex_groups.clear()
for bn in ['Hips','Spine1','Chest']:robe.vertex_groups.new(name=bn)
for v in robe.data.vertices:
 z=v.co.z;t=max(0,min(1,(z-.40)/.09));robe.vertex_groups['Chest'].add([v.index],t,'REPLACE');robe.vertex_groups['Hips'].add([v.index],1-t,'REPLACE')
solid=robe.modifiers.new('Fabric thickness','SOLIDIFY');solid.thickness=.004
# One broad split-tail scarf. This is its designed rest shape, NOT a simulated motion.
verts=[];faces=[];rows=17;cols=8
for i in range(rows):
 t=i/(rows-1);cy=.08+.58*t;cz=.60-.07*t+.025*math.sin(math.pi*t);cx=.035+.12*t
 for j in range(cols+1):
  u=j/cols;notch=.055*(1-abs(2*u-1)) if i==rows-1 else 0
  verts.append((cx,cy-notch,cz+(u-.5)*(.09+.045*t)))
for i in range(rows-1):
 for j in range(cols):
  a=i*(cols+1)+j;faces.append((a,a+1,a+cols+2,a+cols+1))
scarf=mesh('ArtScarfTail',verts,faces,2,'Chest');sol=scarf.modifiers.new('Fabric thickness','SOLIDIFY');sol.thickness=.003
pin=scarf.vertex_groups.new(name='ClothPin');pin.add(list(range(cols+1)),1,'REPLACE')
# Replace noisy UV-classified gold eye patches with two real rectangular 3D eye plates.
for p in hero.data.polygons:
 if p.material_index==3 and sum(original[i].z for i in p.vertices)/len(p.vertices)>.68:p.material_index=1
for sign in [-1,1]:
 x=sign*.062;z=.738;y=-.151
 vs=[(x+dx,y+dy,z+dz) for dx in [-.014,.014] for dy in [-.005,.005] for dz in [-.038,.038]]
 mesh('ArtEye'+str(sign),vs,[(0,1,3,2),(4,6,7,5),(0,4,5,1),(2,3,7,6),(1,5,7,3),(0,2,6,4)],3,'Head')

# Relax arms for a neutral style review, not authored running animation.
for side,sign in [('Left',1),('Right',-1)]:
 pb=rig.pose.bones[side+'Arm'];rest=pb.bone.matrix_local
 pb.matrix=Matrix.Translation(rest.translation)@Matrix.Rotation(sign*math.radians(65),4,'Y')@rest.to_3x3().to_4x4()
bpy.context.view_layer.update()
s.render.resolution_x=s.render.resolution_y=384;s.cycles.samples=12;s.cycles.use_denoising=False;s.render.film_transparent=True
cam.data.ortho_scale=1.55
for angle in [30,45,60,90,180]:
 a=math.radians(angle);offset=Vector((math.cos(a),-math.sin(a),math.tan(math.radians(5))))*3
 cam.rotation_euler=(-offset).to_track_quat('-Z','Y').to_euler();cam.location=offset+cam.rotation_euler.to_matrix()@Vector((0,.5166667,0))
 s.render.filepath=str(O/f'view-{angle}.png');bpy.ops.render.render(write_still=True)
cam.rotation_euler=(Vector((math.cos(math.pi/3),-math.sin(math.pi/3),math.tan(math.radians(5))))*-3).to_track_quat('-Z','Y').to_euler()
cam.location=Vector((1.5,-2.598076,.262466))+cam.rotation_euler.to_matrix()@Vector((0,.5166667,0))
bpy.ops.wm.save_as_mainfile(filepath=str(O/'hero.blend'),compress=True)
# Export only the editable character parts and rig.
bpy.ops.object.select_all(action='DESELECT')
for ob in [hero,robe,scarf,rig]+[o for o in s.objects if o.name.startswith('ArtEye')]:ob.select_set(True)
bpy.ops.export_scene.gltf(filepath=str(O/'hero.glb'),use_selection=True,export_animations=False)
changed=[i for i,(a,v) in enumerate(zip(original,hero.data.vertices)) if (a-v.co).length>1e-8]
(O/'build.json').write_text(json.dumps({'base':'Actual Tripo A via art-style-prototype/prototype.blend','original_vertices':len(original),'modified_vertices':len(changed),'min_modified_original_z':min(original[i].z for i in changed),'limb_geometry_unchanged':all((original[i]-v.co).length<1e-8 for i,v in enumerate(hero.data.vertices) if original[i].z<=.64),'new_parts':['ArtRobe','ArtScarfTail'],'motion':'neutral static pose only; no new Kimodo generation','cloth':'designed rest shape only; no simulation or physics validation','camera_angles':[30,45,60,90,180]},indent=2))

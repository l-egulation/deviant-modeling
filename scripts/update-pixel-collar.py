"""Refresh skin weights only; preserve approved mesh, skeleton and animation."""
import bpy,numpy as np,sys
from pathlib import Path
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'scripts'))
from pixel_skin import skin_fields
for file in ['tripo-pixel-rig.blend','pixel-run.blend']:
 bpy.ops.wm.open_mainfile(filepath=str(R/'outputs'/file))
 h=bpy.data.objects['TripoPixel_Character'];rig=bpy.data.objects['TripoPixel_Rig']
 p=np.array([v.co[:] for v in h.data.vertices])
 labels=np.array([next(h.vertex_groups[g.group].name[7:] for g in v.groups if h.vertex_groups[g.group].name.startswith('Region_')) for v in h.data.vertices])
 names=[b.name for b in rig.data.bones if b.use_deform]
 W=skin_fields(p,labels,names)
 for j,n in enumerate(names):
  vg=h.vertex_groups[n];vg.remove(list(range(len(p))))
  for i in np.flatnonzero(W[:,j]>1e-8):vg.add([int(i)],float(W[i,j]),'REPLACE')
 assert np.max(np.abs(W.sum(1)-1))<1e-6
 bpy.ops.wm.save_as_mainfile(filepath=str(R/'outputs'/file),compress=True)
 if file=='pixel-run.blend':
  for frame in [10,25,40,55]:
   bpy.context.scene.frame_set(frame)
   bpy.context.scene.render.filepath=str(R/f'outputs/pixel-run-pose-{frame}.png')
   bpy.ops.render.render(write_still=True)

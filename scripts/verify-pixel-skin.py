"""All-frame stretch and attachment audit, independent of the builder's pose samples."""
import bpy,numpy as np,json,itertools
from pathlib import Path
R=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(R/'outputs/tripo-pixel-rig.blend'))
s=bpy.context.scene;h=bpy.data.objects['TripoPixel_Character'];rig=bpy.data.objects['TripoPixel_Rig']
p=np.array([v.co[:] for v in h.data.vertices]);edges=np.array([e.vertices[:] for e in h.data.edges])
length=np.linalg.norm(p[edges[:,0]]-p[edges[:,1]],axis=1);valid=length>1e-4
labels=[]
for v in h.data.vertices:labels.append(next(h.vertex_groups[g.group].name[7:] for g in v.groups if h.vertex_groups[g.group].name.startswith('Region_')))
labels=np.array(labels);position_groups={}
for i,point in enumerate(p):position_groups.setdefault(tuple(np.round(point,6)),{}).setdefault(labels[i],i)
pairs={}
for group in position_groups.values():
 for a,b in itertools.combinations(sorted(group),2):pairs.setdefault(a+' / '+b,[]).append((group[a],group[b]))
pairs={k:np.array(v) for k,v in pairs.items()};gaps={k:0. for k in pairs};gap_locations={}
peak=0;peakframe=0;over=0;robe_knee_displacement=0;scarf_arm_displacement=0
for f in range(1,s.frame_end+1):
 s.frame_set(f);bpy.context.view_layer.update();q=np.array([v.co[:] for v in h.evaluated_get(bpy.context.evaluated_depsgraph_get()).data.vertices])
 ratios=np.linalg.norm(q[edges[:,0]]-q[edges[:,1]],axis=1)[valid]/length[valid]
 if ratios.max()>peak:peak=float(ratios.max());peakframe=f
 over=max(over,int((ratios>2).sum()))
 for k,e in pairs.items():
  distances=np.linalg.norm(q[e[:,0]]-q[e[:,1]],axis=1);j=int(np.argmax(distances))
  if distances[j]>gaps[k]:gaps[k]=float(distances[j]);gap_locations[k]={'frame':f,'rest':p[e[j,0]].tolist()}
 if f==21:scarf_arm_displacement=float(np.linalg.norm(q[labels=='Scarf']-p[labels=='Scarf'],axis=1).max())
 if f==41:robe_knee_displacement=float(np.linalg.norm(q[labels=='Robe']-p[labels=='Robe'],axis=1).max())
report={'frames':s.frame_end,'edge_min_rest_length_m':.0001,'edge_stretch_max':peak,'peak_frame':peakframe,'max_edges_over_2x':over,'interface_gaps_m':gaps,'interface_peak_locations':gap_locations,'scarf_displacement_in_arm_test_m':scarf_arm_displacement,'robe_displacement_in_knee_test_m':robe_knee_displacement,'cloth_collision_verified':False}
(R/'docs/logs/pixel-skin-validation.json').write_text(json.dumps(report,indent=2));print(json.dumps(report))
assert over==0 and peak<2, 'Excessive edge stretch in the joint-test range'
assert gaps.get('Arm.L / Robe',0)<1e-5 and gaps.get('Arm.R / Robe',0)<1e-5, 'Sleeve attachment opened'
assert scarf_arm_displacement<1e-5 and robe_knee_displacement<1e-5, 'Garment driven by unrelated limb'

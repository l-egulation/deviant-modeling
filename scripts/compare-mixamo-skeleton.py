"""Project actual sampled bones for source / previous / proportional comparison."""
import json
from pathlib import Path
import numpy as np
from PIL import Image,ImageDraw
ROOT=Path(__file__).resolve().parents[1]
data=json.loads((ROOT/'docs/logs/hero-mixamo-run-skeleton.json').read_text())
frames=[]
for i in range(22):
 im=Image.new('RGB',(1140,480),(237,239,242));draw=ImageDraw.Draw(im)
 for col,(key,title,height) in enumerate([('source','Mixamo original',1.7),('previous','Previous transfer',.94),('target','Character proportions / source angles',.94)]):
  bones=data[key][i];hip=np.array(bones['Hips'][0]);scale=315/height
  draw.text((col*380+16,18),title,fill=(25,30,40))
  for name,ends in bones.items():
   pts=np.array(ends)-hip
   xy=[(int(col*380+190+p[1]*scale),int(270-p[2]*scale)) for p in pts]
   color=(24,131,155) if name.startswith('Left') else (213,112,45) if name.startswith('Right') else (64,72,90)
   draw.line(xy,fill=color,width=5)
   for x,y in xy:draw.ellipse((x-4,y-4,x+4,y+4),fill=color)
  draw.text((col*380+16,447),'Side view / pelvis centered / 30 fps',fill=(65,70,80))
 draw.text((16,468),f'Original phase {i+1}/22 | teal: left, orange: right | body height normalized for display',fill=(65,70,80))
 frames.append(im)
frames[0].save(ROOT/'outputs/hero-mixamo-run-skeleton.gif',save_all=True,append_images=frames[1:],duration=[30,30,40]*7+[30],loop=0)
frames[7].save(ROOT/'outputs/hero-mixamo-run-skeleton.png')
def angle(a,b):
 a=np.array(a);b=np.array(b);return np.degrees(np.arccos(np.clip(a@b/np.linalg.norm(a)/np.linalg.norm(b),-1,1)))
report={}
for side in ('Left','Right'):
 for a,b in [('Arm','ForeArm'),('UpLeg','Leg')]:
  err=[]
  for source,old in zip(data['source'],data['previous']):
   def v(d,n):return np.array(d[n][1])-d[n][0]
   err.append(abs(angle(v(source,side+a),v(source,side+b))-angle(v(old,side+a),v(old,side+b))))
  report[side+a]={'previous_bend_error_max_degrees':max(err),'median':float(np.median(err))}
(ROOT/'docs/logs/hero-mixamo-run-angle-comparison.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report))


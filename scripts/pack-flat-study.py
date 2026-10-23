from pathlib import Path
from PIL import Image,ImageDraw
import numpy as np,json
R=Path(__file__).resolve().parents[1];O=R/'outputs/pixel-flat-study'
meta=json.loads((O/'study.json').read_text());pal=np.array([[int(c[i:i+2],16) for i in (0,2,4)] for c in meta['palette']])
board=Image.new('RGB',(1152,840),'#454953');report={}
for row,mode in enumerate(['flat','patch']):
 for col,angle in enumerate([30,45,60]):
  name=f'{mode}-{angle}';a=np.array(Image.open(O/f'{name}.png').convert('RGBA').resize((128,128),Image.Resampling.NEAREST))
  idx=((a[:,:,:3].astype(int)[:,:,None,:]-pal)**2).sum(3).argmin(2);a[:,:,:3]=pal[idx];a[:,:,3]=np.where(a[:,:,3]>=128,255,0);a[a[:,:,3]==0,:3]=0
  im=Image.fromarray(a);im.save(O/f'{name}-128.png')
  assert set(np.unique(a[:,:,3])).issubset({0,255})
  report[name]={'colors':len(set(map(tuple,a[a[:,:,3]>0,:3]))),'bounds':im.getbbox()}
  tile=im.resize((384,384),Image.Resampling.NEAREST);board.paste(tile,(col*384,row*420+36),tile)
  ImageDraw.Draw(board).text((col*384+12,row*420+12),f'{mode.upper()} / {angle} DEG',fill='white')
board.save(O/'options.png')
# Same-pose before/after, plus unchanged team reference at the left.
comparison=Image.new('RGB',(1152,420),'#454953')
reference=Image.open(R/'outputs/art-style-rules/team-native.png').convert('RGBA')
ref=Image.new('RGBA',(128,128));ref.paste(reference,(40,48),reference)
for j,(im,title) in enumerate([(ref,'TEAM REFERENCE / IDLE'),(Image.open(R/'outputs/pixel-run-sprites/128px/004.png'),'BEFORE / SAME RUN POSE'),(Image.open(O/'patch-60-128.png'),'AFTER / FLAT PATCHES, 60 DEG')]):
 tile=im.resize((384,384),Image.Resampling.NEAREST);comparison.paste(tile,(j*384,36),tile);ImageDraw.Draw(comparison).text((j*384+10,12),title,fill='white')
comparison.save(O/'comparison.png');(O/'validation.json').write_text(json.dumps(report,indent=2))

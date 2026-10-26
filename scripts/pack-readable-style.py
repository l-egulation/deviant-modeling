"""Fixed-grid pixel previews for pose/camera readability review."""
from pathlib import Path
import json
import numpy as np
from PIL import Image,ImageDraw,ImageOps
R=Path(__file__).resolve().parents[1]
P=np.array([[int(c[i:i+2],16) for i in (0,2,4)] for c in ['FDEEDA','D2B396','1B1616','025673','02648C','EBA516']])
def pixel(path):
 a=np.array(Image.open(path).convert('RGBA').resize((128,128),Image.Resampling.NEAREST));mask=a[:,:,3]>=128
 idx=((a[:,:,:3].astype(int)[:,:,None,:]-P)**2).sum(3).argmin(2)
 a[:,:,:3]=P[idx];a[:,:,3]=mask*255;a[~mask,:3]=0
 return ImageOps.mirror(Image.fromarray(a))
def board(images,labels):
 b=Image.new('RGB',(384*len(images),420),'#454953');d=ImageDraw.Draw(b)
 for k,(im,label) in enumerate(zip(images,labels)):
  q=im.crop((24,24,104,112)).resize((320,352),Image.Resampling.NEAREST);b.paste(q,(384*k+32,44),q);d.text((384*k+15,14),label,fill='white')
 return b
O=R/'outputs/pixel-readable-study'
imgs=[pixel(O/f'raw/angle{a}/designed/001.png') for a in [60,75,90]]
board(imgs,['60 DEGREES','75 DEGREES','90 DEGREES']).save(O/'camera-comparison.png')
O=R/'outputs/pixel-readable-style'
if (O/'render-validation.json').exists():
 meta=json.loads((O/'render-validation.json').read_text());report={}
 meta['camera_degrees_from_side']='per-clip angle'
 meta['shadows']['hood']='side wedge x > .23 + .12*(z-.65)'
 meta['limitations']=['geometry preserved during rendering; new idle pose and re-simulated cloth','no AI images or per-frame cleanup','loop seam not guaranteed']
 (O/'render-validation.json').write_text(json.dumps(meta,indent=2))
 for tag,old in [('idle','pixel-idle'),('run','pixel-run')]:
  frames=[];boards=[];dest=O/tag;dest.mkdir(parents=True,exist_ok=True)
  for f in meta[tag]['frames']:
   im=pixel(O/f'raw/{tag}/designed/{f:03d}.png');im.save(dest/f'{f:03d}.png');frames.append(im)
   before=Image.open(R/f'outputs/pixel-painted-style/{old}/designed/{f:03d}.png').convert('RGBA')
   boards.append(board([before,im],['BEFORE','READABLE POSE / SHADOWS']))
   box=im.getbbox();assert min(box[:2])>0 and max(box[2:])<128
  timing=[10*(round((j+1)*100/30)-round(j*100/30)) for j in range(len(frames))]
  indexed=[]
  for im in frames:
   a=np.array(im);idx=((a[:,:,:3].astype(int)[:,:,None,:]-P)**2).sum(3).argmin(2)
   p=Image.fromarray(np.where(a[:,:,3]>0,idx+1,0).astype('uint8'),'P');p.putpalette([0,0,0]+P.ravel().tolist()+[0]*747);indexed.append(p)
  indexed[0].save(dest/'preview.gif',save_all=True,append_images=indexed[1:],duration=timing,loop=0,transparency=0,disposal=2,optimize=False)
  boards[0].save(O/f'{tag}-comparison.png');boards[0].save(O/f'{tag}-comparison.gif',save_all=True,append_images=boards[1:],duration=timing,loop=0)
  sheet=Image.new('RGBA',(768,128*((len(frames)+5)//6)))
  for j,im in enumerate(frames):sheet.paste(im,((j%6)*128,(j//6)*128))
  sheet.save(dest/'sheet.png')
  gif=Image.open(dest/'preview.gif');duration=0
  for j in range(gif.n_frames):gif.seek(j);duration+=gif.info['duration']
  assert duration==sum(timing)
  report[tag]={'source_frames':len(frames),'duration_ms':duration,'canvas':[128,128],'clipping':False,'palette_colors':6,'binary_alpha':True,'timing':'30fps rounded to GIF centiseconds'}
 (O/'pixel-validation.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2))

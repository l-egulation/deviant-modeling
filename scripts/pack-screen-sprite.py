"""Keep the shared framing while packing the camera-specific shape study."""
from pathlib import Path
from PIL import Image,ImageDraw,ImageOps
import numpy as np,json,zipfile
R=Path(__file__).resolve().parents[1];O=R/'outputs/pixel-screen-study';meta=json.loads((O/'study.json').read_text())
pal=np.array([[int(c[i:i+2],16) for i in (0,2,4)] for c in meta['palette']]);dur=[round((i+1)*100/30)*10-round(i*100/30)*10 for i in range(22)]
frames={};report={}
def indexed(im):
 a=np.array(im);idx=((a[:,:,:3].astype(int)[:,:,None,:]-pal)**2).sum(3).argmin(2)+1;idx[a[:,:,3]==0]=0
 out=Image.fromarray(idx.astype('uint8'),'P');out.putpalette([0,0,0]+pal.ravel().tolist()+[0]*(768-21));return out
for mode in ['before','after']:
 folder=O/f'{mode}-128';folder.mkdir(exist_ok=True);frames[mode]=[];bounds=[]
 for i in range(22):
  im=ImageOps.mirror(Image.open(O/f'{mode}/{i:03d}.png').convert('RGBA')).resize((128,128),Image.Resampling.NEAREST);a=np.array(im)
  idx=((a[:,:,:3].astype(int)[:,:,None,:]-pal)**2).sum(3).argmin(2);a[:,:,:3]=pal[idx];a[:,:,3]=np.where(a[:,:,3]>=128,255,0);a[a[:,:,3]==0,:3]=0
  im=Image.fromarray(a);b=im.getbbox();assert b and min(b[:2])>0 and max(b[2:])<128
  assert set(map(tuple,a[a[:,:,3]>0,:3])).issubset(set(map(tuple,pal)))
  im.save(folder/f'{i:03d}.png');frames[mode].append(im);bounds.append(b)
 sheet=Image.new('RGBA',(768,512))
 for i,im in enumerate(frames[mode]):sheet.paste(im,((i%6)*128,(i//6)*128))
 sheet.save(O/f'{mode}-sheet.png');gif=[indexed(im) for im in frames[mode]]
 gif[0].save(O/f'{mode}.gif',save_all=True,append_images=gif[1:],duration=dur,loop=0,transparency=0,disposal=2,optimize=False)
 assert Image.open(O/f'{mode}.gif').n_frames==22
 report[mode]={'frames':22,'canvas':128,'palette_only':True,'alpha':[0,255],'bounds':bounds}
ref=Image.open(R/'outputs/art-style-rules/team-native.png').convert('RGBA');reference=Image.new('RGBA',(128,128));reference.paste(ref,(40,48),ref)
boards=[]
for i in range(22):
 board=Image.new('RGB',(1152,420),'#454953')
 for j,(im,title) in enumerate([(reference,'TEAM REFERENCE / IDLE'),(frames['before'][i],'BEFORE / SAME CAMERA'),(frames['after'][i],'AFTER / SHAPE + GRAPHIC EYES')]):
  tile=im.resize((384,384),Image.Resampling.NEAREST);board.paste(tile,(j*384,36),tile);ImageDraw.Draw(board).text((j*384+10,12),title,fill='white')
 boards.append(board)
boards[4].save(O/'comparison.png');boards[0].save(O/'comparison.gif',save_all=True,append_images=boards[1:],duration=dur,loop=0)
sheet=Image.new('RGB',(768,540),'#454953')
for i,im in enumerate(frames['after']):
 x=i%6*128;y=i//6*135;sheet.paste(im,(x,y),im);ImageDraw.Draw(sheet).text((x+3,y+2),str(i),fill='white')
sheet.save(O/'contact-sheet.png');(O/'validation.json').write_text(json.dumps(report,indent=2))
with zipfile.ZipFile(R/'outputs/pixel-screen-study.zip','w',zipfile.ZIP_DEFLATED) as z:
 for path in O.rglob('*'):
  if path.is_file() and path.suffix!='.blend' and path.parent.name not in ['before','after']:z.write(path,path.relative_to(O))
print('PASS: 22 frames, shared 128px canvas, six-color palette, binary alpha, no clipping')

"""Pack shared-palette transparent frames and inspection previews."""
from pathlib import Path
from PIL import Image,ImageDraw
import numpy as np,json,zipfile
R=Path(__file__).resolve().parents[1];O=R/'outputs/pixel-run-sprites'
meta=json.loads((O/'capture.json').read_text());pal=np.array([[int(h[i:i+2],16) for i in (0,2,4)] for h in meta['palette']],dtype=np.int32)
durations=[round((i+1)*100/30)*10-round(i*100/30)*10 for i in range(22)]
def pixel(im,size):
 a=np.array(im.convert('RGBA').resize((size,size),Image.Resampling.NEAREST))
 idx=((a[:,:,:3].astype(np.int32)[:,:,None,:]-pal)**2).sum(3).argmin(2)
 a[:,:,:3]=pal[idx];a[:,:,3]=np.where(a[:,:,3]>=128,255,0)
 a[a[:,:,3]==0,:3]=0
 return Image.fromarray(a)
def indexed(im):
 a=np.array(im);idx=((a[:,:,:3].astype(np.int32)[:,:,None,:]-pal)**2).sum(3).argmin(2)+1;idx[a[:,:,3]==0]=0
 out=Image.fromarray(idx.astype('uint8'),'P');out.putpalette([0,0,0]+pal.ravel().tolist()+[0]*(768-21));out.info['transparency']=0
 return out
allframes={};report={}
for label,size in [('128px',128),('coarse',64)]:
 folder=O/label;folder.mkdir(exist_ok=True);frames=[];bounds=[]
 for i in range(22):
  im=pixel(Image.open(O/f'render/{i:03d}.png'),size)
  if size==64:im=im.resize((128,128),Image.Resampling.NEAREST)
  im.save(folder/f'{i:03d}.png');frames.append(im);bounds.append(im.getbbox())
  assert im.getbbox() and all(v>0 for v in im.getbbox()[:2]) and all(v<128 for v in im.getbbox()[2:])
  a=np.array(im);assert set(np.unique(a[:,:,3])).issubset({0,255})
  assert set(map(tuple,a[a[:,:,3]>0,:3])).issubset(set(map(tuple,pal)))
 sheet=Image.new('RGBA',(768,512))
 for i,im in enumerate(frames):sheet.paste(im,((i%6)*128,(i//6)*128))
 sheet.save(O/f'spritesheet-{label}.png')
 gif=[indexed(im) for im in frames];gif[0].save(O/f'run-{label}.gif',save_all=True,append_images=gif[1:],duration=durations,loop=0,transparency=0,disposal=2,optimize=False)
 check=Image.open(O/f'run-{label}.gif');assert check.n_frames==22
 allframes[label]=frames;report[label]={'frames':22,'bounds':bounds,'palette_colors':6,'alpha':[0,255],'logical_resolution':size,'canvas':128}
originalsheet=Image.new('RGBA',(2304,1536))
for i in range(22):originalsheet.paste(Image.open(O/f'original/{i:03d}.png'),((i%6)*384,(i//6)*384))
originalsheet.save(O/'spritesheet-original.png')
boards=[]
for i in range(22):
 b=Image.new('RGB',(1152,420),'#454953');d=ImageDraw.Draw(b)
 tiles=[Image.open(O/f'original/{i:03d}.png'),allframes['128px'][i].resize((384,384),Image.Resampling.NEAREST),allframes['coarse'][i].resize((384,384),Image.Resampling.NEAREST)]
 for j,(im,title) in enumerate(zip(tiles,['3D CAPTURE','128px / SIX COLORS','64px GRID / 128px CANVAS'])):
  b.paste(im,(j*384,36),im);d.text((j*384+12,12),title,fill='white')
 boards.append(b)
boards[4].save(O/'comparison.png')
boards[0].save(O/'comparison.gif',save_all=True,append_images=boards[1:],duration=durations,loop=0)
contact=Image.new('RGB',(768,540),'#454953')
for i,im in enumerate(allframes['128px']):
 x=(i%6)*128;y=(i//6)*135;contact.paste(im,(x,y),im);ImageDraw.Draw(contact).text((x+3,y+2),str(i),fill='white')
contact.save(O/'contact-sheet.png')
meta['sheet']={'columns':6,'rows':4,'cell':[128,128],'order':'left-to-right then top-to-bottom','empty_last_cells':2}
meta['gif_duration_ms']=sum(durations);meta['note']='GIF uses centisecond timing (730ms); game playback uses exact 30fps (733.333ms). Cloth loop seam is not guaranteed.'
(O/'capture.json').write_text(json.dumps(meta,indent=2));(O/'validation.json').write_text(json.dumps(report,indent=2))
with zipfile.ZipFile(R/'outputs/pixel-run-sprites.zip','w',zipfile.ZIP_DEFLATED) as z:
 for path in O.rglob('*'):
  if path.is_file() and 'render' not in path.relative_to(O).parts:z.write(path,path.relative_to(O))
print(json.dumps({'frames':22,'fps':30,'gif_ms':sum(durations),'validation':'PASS','same_phase_cloth_drift_m':meta['same_phase_cloth_drift_m']}))

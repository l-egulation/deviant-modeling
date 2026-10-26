"""Original-model idle in the accepted large-pixel, broad-shadow palette."""
from pathlib import Path
from PIL import Image,ImageDraw,ImageOps
import numpy as np,json,zipfile
R=Path(__file__).resolve().parents[1];S=R/'outputs/pixel-idle-sprites';O=R/'outputs/pixel-idle';(O/'frames').mkdir(parents=True,exist_ok=True)
meta=json.loads((S/'capture.json').read_text());N=meta['frame_count'];assert N==90
pal=np.array([[int(c[i:i+2],16) for i in (0,2,4)] for c in meta['palette']]);dur=[30,30,40]*30
def regions(mask):
 seen=np.zeros_like(mask);out=np.zeros_like(mask)
 for y,x in zip(*np.where(mask)):
  if seen[y,x]:continue
  stack=[(y,x)];seen[y,x]=True;area=[]
  while stack:
   yy,xx=stack.pop();area.append((yy,xx))
   for dy,dx in [(0,1),(0,-1),(1,0),(-1,0)]:
    ny,nx=yy+dy,xx+dx
    if 0<=ny<64 and 0<=nx<64 and mask[ny,nx] and not seen[ny,nx]:seen[ny,nx]=True;stack.append((ny,nx))
  if len(area)>=5:
   for yy,xx in area:out[yy,xx]=True
 return out
def expanded(mask):
 a=np.pad(mask,1);return np.logical_or.reduce([a[y:y+64,x:x+64] for y in range(3) for x in range(3)])
inputs=[];masks=[]
for i in range(N):
 a=np.array(Image.open(S/f'render/{i:03d}.png').convert('RGBA').resize((64,64),Image.Resampling.NEAREST));a[:,:,3]=np.where(a[:,:,3]>=128,255,0)
 idx=((a[:,:,:3].astype(int)[:,:,None,:]-pal)**2).sum(3).argmin(2);inputs.append((a,idx));masks.append(regions((idx==1)&(a[:,:,3]>0)))
frames=[];bounds=[];indexed=[]
for i,(a,idx) in enumerate(inputs):
 support=np.logical_or.reduce([expanded(masks[j]) for j in [i-1,i+1] if 0<=j<N]);shadow=regions(masks[i]&support)
 idx=idx.copy();idx[idx==1]=0;idx[idx==4]=3;idx[shadow]=1
 a[:,:,:3]=pal[idx];a[a[:,:,3]==0,:3]=0
 im=ImageOps.mirror(Image.fromarray(a).resize((128,128),Image.Resampling.NEAREST));im.save(O/f'frames/{i:03d}.png');frames.append(im)
 box=im.getbbox();assert box and min(box[:2])>0 and max(box[2:])<128;bounds.append(box)
 ids=np.where(a[:,:,3]>0,idx+1,0).astype('uint8');gif=ImageOps.mirror(Image.fromarray(ids,'P').resize((128,128),Image.Resampling.NEAREST));gif.putpalette([0,0,0]+pal.ravel().tolist()+[0]*(768-21));indexed.append(gif)
indexed[0].save(O/'idle.gif',save_all=True,append_images=indexed[1:],duration=dur,loop=0,transparency=0,disposal=2,optimize=False)
sheet=Image.new('RGBA',(1280,1152))
for i,im in enumerate(frames):sheet.paste(im,((i%10)*128,(i//10)*128))
sheet.save(O/'spritesheet.png')
# Preserve teammate GIF timing and use one fixed crop for all reference frames.
ref=Image.open(R/'assets/team-dagger-idle.gif');references=[];times=[]
for i in range(ref.n_frames):
 ref.seek(i);references.append(ref.convert('RGBA').resize((127,148),Image.Resampling.NEAREST));times.append(ref.info.get('duration',160))
boxes=[im.getbbox() for im in references];box=(min(b[0] for b in boxes),min(b[1] for b in boxes),max(b[2] for b in boxes),max(b[3] for b in boxes))
boards=[];previews=[]
for i,im in enumerate(frames):
 elapsed=(i*1000/30)%sum(times);j=0
 while elapsed>=times[j]:elapsed-=times[j];j+=1
 tile=references[j].crop(box).resize(((box[2]-box[0])*4,(box[3]-box[1])*4),Image.Resampling.NEAREST)
 board=Image.new('RGB',(768,420),'#454953');board.paste(tile,((384-tile.width)//2,372-tile.height),tile)
 ours=im.resize((384,384),Image.Resampling.NEAREST);board.paste(ours,(384,36),ours)
 d=ImageDraw.Draw(board);d.text((12,12),'TEAM / DAGGER IDLE',fill='white');d.text((396,12),'OUR MODEL / BREATHING IDLE',fill='white');boards.append(board)
 bg=Image.new('RGB',(384,384),'#454953');bg.paste(ours,(0,0),ours);previews.append(bg)
boards[0].save(O/'comparison.png');boards[0].save(O/'comparison.gif',save_all=True,append_images=boards[1:],duration=dur,loop=0)
previews[0].save(O/'preview.gif',save_all=True,append_images=previews[1:],duration=dur,loop=0)
if (O/'before-idle.gif').exists():
 previous=Image.open(O/'before-idle.gif');old=[];old_times=[]
 for j in range(previous.n_frames):
  previous.seek(j);old.append(previous.convert('RGBA'));old_times.append(previous.info['duration'])
 changes=[]
 for i,im in enumerate(frames):
  elapsed=i*1000/30;j=0
  while j<len(old)-1 and elapsed>=old_times[j]:elapsed-=old_times[j];j+=1
  board=Image.new('RGB',(768,420),'#454953')
  for x,tile in [(0,old[j]),(384,im)]:
   tile=tile.resize((384,384),Image.Resampling.NEAREST);board.paste(tile,(x,36),tile)
  d=ImageDraw.Draw(board);d.text((12,12),'BEFORE',fill='white');d.text((396,12),'READY STANCE',fill='white');changes.append(board)
 changes[0].save(O/'pose-comparison.png');changes[0].save(O/'pose-comparison.gif',save_all=True,append_images=changes[1:],duration=dur,loop=0)
contact=Image.new('RGB',(768,540),'#454953')
for j,i in enumerate(range(0,90,5)):
 x=j%6*128;y=j//6*180;contact.paste(frames[i],(x,y+25),frames[i]);ImageDraw.Draw(contact).text((x+4,y+5),str(i),fill='white')
contact.save(O/'contact-sheet.png')
check=Image.open(O/'idle.gif');duration=0
for i in range(check.n_frames):check.seek(i);duration+=check.info['duration']
assert duration==3000
meta.update({'canvas':[128,128],'logical_grid':[64,64],'pixel_block_size':2,'palette_used':['FDEEDA','D2B396','1B1616','025673','EBA516'],'gif_duration_ms':duration,'gif_stored_frames':check.n_frames,'bounds':bounds,'sheet':{'columns':10,'rows':9,'cell':[128,128]},'weapon_added':False,'mirrored_for_right_facing':True,'reference_display':'fixed crop, native pixels enlarged4x; ours logical pixels enlarged6x; approximately similar displayed height','loop_verified':False})
(O/'capture.json').write_text(json.dumps(meta,indent=2))
with zipfile.ZipFile(R/'outputs/pixel-idle.zip','w',zipfile.ZIP_DEFLATED) as z:
 for p in O.rglob('*'):
  if p.is_file():z.write(p,p.relative_to(O))
print('PASS: 90 frames, 128px, binary alpha, no clipping, 3 seconds; GIF may merge identical frames')

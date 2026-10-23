"""Simplify the ORIGINAL capture: fixed 2px blocks, no geometry or pose edits."""
from pathlib import Path
from PIL import Image,ImageDraw
import numpy as np,json,zipfile
R=Path(__file__).resolve().parents[1];source=R/'outputs/pixel-run-sprites';O=R/'outputs/pixel-simple-run';(O/'frames').mkdir(parents=True,exist_ok=True)
meta=json.loads((source/'capture.json').read_text());pal=np.array([[int(c[i:i+2],16) for i in (0,2,4)] for c in meta['palette']])
dur=[round((i+1)*100/30)*10-round(i*100/30)*10 for i in range(22)]
frames=[];boards=[];validation=[]
for i in range(22):
 # The prior coarse capture has exactly the approved, unmodified silhouette.
 old=Image.open(source/f'coarse/{i:03d}.png').convert('RGBA')
 small=old.resize((64,64),Image.Resampling.NEAREST);a=np.array(small)
 idx=((a[:,:,:3].astype(int)[:,:,None,:]-pal)**2).sum(3).argmin(2)
 # Remove volume shading, keeping original material boundaries and all eyes.
 idx[idx==1]=0;idx[idx==4]=3
 a[:,:,:3]=pal[idx];a[a[:,:,3]==0,:3]=0
 im=Image.fromarray(a).resize((128,128),Image.Resampling.NEAREST)
 assert np.array_equal(np.array(im)[:,:,3],np.array(old)[:,:,3])
 assert im.getbbox()==old.getbbox()
 assert np.array_equal(np.array(im)[::2,::2],np.array(im)[1::2,1::2])
 im.save(O/f'frames/{i:03d}.png');frames.append(im)
 colors=set(map(tuple,np.array(im)[np.array(im)[:,:,3]>0,:3]));assert colors.issubset(set(map(tuple,pal[[0,2,3,5]])))
 validation.append({'frame':i,'bounds':im.getbbox(),'colors':len(colors),'alpha_matches_previous_capture':True})
 board=Image.new('RGB',(768,420),'#454953')
 for j,(tile,title) in enumerate([(old,'PREVIOUS CAPTURE / COARSE'),(im,'SAME SHAPE / FLAT COLORS')]):
  tile=tile.resize((384,384),Image.Resampling.NEAREST);board.paste(tile,(j*384,36),tile);ImageDraw.Draw(board).text((j*384+12,12),title,fill='white')
 boards.append(board)
sheet=Image.new('RGBA',(768,512))
for i,im in enumerate(frames):sheet.paste(im,((i%6)*128,(i//6)*128))
sheet.save(O/'spritesheet.png')
indexed=[]
for im in frames:
 a=np.array(im);idx=((a[:,:,:3].astype(int)[:,:,None,:]-pal)**2).sum(3).argmin(2)+1;idx[a[:,:,3]==0]=0
 gif=Image.fromarray(idx.astype('uint8'),'P');gif.putpalette([0,0,0]+pal.ravel().tolist()+[0]*(768-21));indexed.append(gif)
indexed[0].save(O/'run.gif',save_all=True,append_images=indexed[1:],duration=dur,loop=0,transparency=0,disposal=2,optimize=False)
assert Image.open(O/'run.gif').n_frames==22
boards[4].save(O/'comparison.png');boards[0].save(O/'comparison.gif',save_all=True,append_images=boards[1:],duration=dur,loop=0)
preview=[]
for im in frames:
 tile=im.resize((384,384),Image.Resampling.NEAREST);bg=Image.new('RGB',(384,384),'#454953');bg.paste(tile,(0,0),tile);preview.append(bg)
preview[0].save(O/'preview.gif',save_all=True,append_images=preview[1:],duration=dur,loop=0)
meta.update({'source':'outputs/pixel-run-sprites/coarse','geometry_edit':False,'screen_study_used':False,'canvas':[128,128],'logical_grid':[64,64],'pixel_block_size':2,'colors_used':['FDEEDA','1B1616','025673','EBA516'],'simplification':'merge ivory and teal shadow/highlight shades; preserve alpha and material boundaries','validation':validation})
(O/'capture.json').write_text(json.dumps(meta,indent=2))
with zipfile.ZipFile(R/'outputs/pixel-simple-run.zip','w',zipfile.ZIP_DEFLATED) as z:
 for path in O.rglob('*'):
  if path.is_file():z.write(path,path.relative_to(O))
print('PASS: 22 frames; original coarse alpha and bounds unchanged; 128px, 2px blocks, 4 team colors')

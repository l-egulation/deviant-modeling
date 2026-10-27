"""Semantic downsampling and selective part boundaries on a fixed pixel grid."""
from pathlib import Path
import json
import numpy as np
from PIL import Image,ImageDraw
R=Path(__file__).resolve().parents[1];O=R/'outputs/pixel-part-style'
meta=json.loads((O/'part-map.json').read_text());C=np.array(meta['colors'],dtype=np.int32)
P=np.array([[int(c[i:i+2],16) for i in (0,2,4)] for c in ['FDEEDA','D2B396','1B1616','025673','02648C','EBA516']],dtype=np.uint8)
def adjacent(mask):
 p=np.pad(mask,1);return p[:-2,1:-1]|p[2:,1:-1]|p[1:-1,:-2]|p[1:-1,2:]
def board(images,labels):
 b=Image.new('RGB',(384*len(images),420),'#454953');d=ImageDraw.Draw(b)
 for k,(im,label) in enumerate(zip(images,labels)):
  q=im.crop((24,24,104,112)).resize((320,352),Image.Resampling.NEAREST);b.paste(q,(384*k+32,44),q);d.text((384*k+15,14),label,fill='white')
 return b
report={'rules':{'features':'eye/clasp/cuff wins when covering >=3 of 9 subpixels, retains at >=2 when previously visible; restricted to correct neighboring parent part','boundaries':'one-pixel ivory shadow on robe next to sleeve/glove; sleeve next to glove; hood next to face','silhouette':'exact original alpha, never grown','temporal':'visibility-bounded screen-space hysteresis; not motion-compensated'},'clips':{}}
for tag,clip in meta['clips'].items():
 frames=[];boards=[];rows=[];previous=None;dest=O/tag;dest.mkdir(parents=True,exist_ok=True)
 for f in clip['frames']:
  raw=np.array(Image.open(O/f'raw/{tag}/{f:03d}.png').convert('RGBA'))
  rgb=raw[:,:,:3].astype(np.int32)
  ids=((rgb[:,:,None,:]-C[None,None,:,:])**2).sum(3).argmin(2);ids[raw[:,:,3]<128]=0
  # Same 3x3 blocks as the 384->128 centered nearest-neighbor color render.
  counts=np.stack([(ids==i).reshape(128,3,128,3).sum((1,3)) for i in range(len(C))],axis=2)
  center=ids[1::3,1::3].copy();base=np.array(Image.open(R/f'outputs/pixel-readable-style/{tag}/{f:03d}.png').convert('RGBA'))[:,::-1].copy()
  alpha=base[:,:,3]>0
  for feature,parents in [(3,[2,3]),(4,[2,4]),(6,[5,6,7]),(16,[12,14,16]),(17,[13,15,17])]:
   threshold=np.where(previous==feature,2,3) if previous is not None else 3
   take=(counts[:,:,feature]>=threshold)&np.isin(center,parents)&alpha
   center[take]=feature
  # Eyes are graphic marks: fit a small upright block to each visible projection.
  # Do not revive a fully occluded eye or paint outside the black face.
  coverage=counts[:,:,3]+counts[:,:,4]
  unseen=set(map(tuple,np.argwhere(coverage>=2)));components=[]
  while unseen:
   seed=unseen.pop();todo=[seed];component=[seed]
   while todo:
    y,x=todo.pop()
    for dy,dx in [(-1,0),(1,0),(0,-1),(0,1)]:
     q=(y+dy,x+dx)
     if q in unseen:unseen.remove(q);todo.append(q);component.append(q)
   components.append(component)
  components=sorted(components,key=lambda c:sum(coverage[y,x] for y,x in c),reverse=True)[:2]
  components.sort(key=lambda c:np.mean([x for y,x in c]))
  center[np.isin(center,[3,4])]=2
  for eye,component in zip([3,4],components):
   ys,xs=np.array(component).T
   if coverage[ys,xs].sum()<9:continue
   cx=int(round(float(np.average(xs,weights=coverage[ys,xs]))));cy=int(round(float(np.average(ys,weights=coverage[ys,xs]))))
   height=min(4,max(3,int(ys.max()-ys.min()+1)));x0=max(0,cx-1);y0=max(0,cy-height//2)
   block=np.zeros_like(alpha);block[y0:y0+height,x0:x0+2]=True
   allowed=np.isin(center,[2,eye])&alpha
   center[block&allowed]=eye
  previous=center.copy();out=base.copy()
  out[(center==2)&alpha,:3]=P[2]
  original_gold=np.all(base[:,:,:3]==P[5],axis=2)
  out[np.isin(center,[1,2])&original_gold&alpha,:3]=P[2]
  out[np.isin(center,[3,4,6,16,17])&alpha,:3]=P[5]
  # Material regions preserve palette; only meaningful adjacency introduces a seam.
  ivory=(out[:,:,0]==P[0,0])&(out[:,:,1]==P[0,1])&(out[:,:,2]==P[0,2])
  seam=((center==7)&adjacent(np.isin(center,[8,9,10,11])))|(np.isin(center,[8,9])&adjacent(np.isin(center,[10,11])))|((center==1)&adjacent(center==2))
  out[seam&ivory&alpha,:3]=P[1]
  assert np.array_equal(out[:,:,3],base[:,:,3])
  assert all(tuple(c) in {tuple(v) for v in P} for c in np.unique(out[alpha,:3],axis=0))
  im=Image.fromarray(out[:,::-1]);im.save(dest/f'{f:03d}.png');frames.append(im)
  part=np.zeros_like(out);part[:,:,:3]=C[center].astype('uint8');part[:,:,3]=base[:,:,3];partim=Image.fromarray(part[:,::-1])
  before=Image.fromarray(base[:,::-1]);boards.append(board([before,partim,im],['BEFORE','SEMANTIC PART MAP','PART-AWARE OUTPUT']))
  if f==clip['frames'][0]:partim.save(dest/'part-map.png')
  rows.append({'frame':f,'changed_pixels':int(np.any(out!=base,axis=2).sum()),'eye_L_pixels':int(((center==3)&alpha).sum()),'eye_R_pixels':int(((center==4)&alpha).sum()),'cuff_L_pixels':int(((center==16)&alpha).sum()),'cuff_R_pixels':int(((center==17)&alpha).sum())})
 timings=[10*(round((j+1)*100/30)-round(j*100/30)) for j in range(len(frames))]
 indexed=[]
 for im in frames:
  a=np.array(im);idx=((a[:,:,:3].astype(int)[:,:,None,:]-P)**2).sum(3).argmin(2)
  p=Image.fromarray(np.where(a[:,:,3]>0,idx+1,0).astype('uint8'),'P');p.putpalette([0,0,0]+P.ravel().tolist()+[0]*747);indexed.append(p)
 indexed[0].save(dest/'preview.gif',save_all=True,append_images=indexed[1:],duration=timings,loop=0,transparency=0,disposal=2,optimize=False)
 boards[0].save(O/f'{tag}-comparison.png');boards[0].save(O/f'{tag}-comparison.gif',save_all=True,append_images=boards[1:],duration=timings,loop=0)
 sheet=Image.new('RGBA',(768,128*((len(frames)+5)//6)))
 for j,im in enumerate(frames):sheet.paste(im,((j%6)*128,(j//6)*128))
 sheet.save(dest/'sheet.png')
 contact=Image.new('RGB',(1152,420*4),'#454953')
 for k,j in enumerate(np.linspace(0,len(boards)-1,4,dtype=int)):contact.paste(boards[j],(0,k*420))
 contact.save(O/f'{tag}-poses.png')
 report['clips'][tag]={'frames':len(frames),'alpha_unchanged':True,'palette_valid':True,'rows':rows}
report['rules']['eyes']='two largest visible eye components, each fit to 2x3-4 pixel upright block inside face; partial clipping allowed; no occluded eye synthesized; IDs are screen-order, not anatomical left/right'
(O/'validation.json').write_text(json.dumps(report,indent=2));print('PART PACK COMPLETE')

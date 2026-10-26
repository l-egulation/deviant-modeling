"""Compare identical geometry on one fixed pixel grid; no frame cleanup."""
from pathlib import Path
import json
import numpy as np
from PIL import Image, ImageDraw, ImageOps
R=Path(__file__).resolve().parents[1];O=R/'outputs/pixel-painted-style'
meta=json.loads((O/'render-validation.json').read_text())
pal=np.array([[int(c[i:i+2],16) for i in (0,2,4)] for c in meta['palette']])
modes=meta['modes'];all_frames={};report={}
for tag in ['pixel-idle','pixel-run']:
 groups={};alphas={};indices={}
 for mode in modes:
  dest=O/tag/mode;dest.mkdir(parents=True,exist_ok=True);frames=[];masks=[];ids=[]
  for f in meta[tag]['frames']:
   a=np.array(Image.open(O/'raw'/tag/mode/f'{f:03d}.png').convert('RGBA').resize((128,128),Image.Resampling.NEAREST))
   mask=a[:,:,3]>=128;idx=((a[:,:,:3].astype(int)[:,:,None,:]-pal)**2).sum(3).argmin(2)
   a[:,:,:3]=pal[idx];a[:,:,3]=np.where(mask,255,0);a[~mask,:3]=0
   im=ImageOps.mirror(Image.fromarray(a));im.save(dest/f'{f:03d}.png');frames.append(im);masks.append(mask);ids.append(idx)
   assert im.getbbox() and min(im.getbbox()[:2])>0 and max(im.getbbox()[2:])<128
  groups[mode]=frames;alphas[mode]=masks;indices[mode]=ids
  indexed=[]
  for idx,mask in zip(ids,masks):
   p=ImageOps.mirror(Image.fromarray(np.where(mask,idx+1,0).astype('uint8'),'P'));p.putpalette([0,0,0]+pal.ravel().tolist()+[0]*(768-21));indexed.append(p)
  if True:
   indexed[0].save(dest/'preview.gif',save_all=True,append_images=indexed[1:],duration=[10*(round((j+1)*100/30)-round(j*100/30)) for j in range(len(indexed))],loop=0,transparency=0,disposal=2,optimize=False)
   gif=Image.open(dest/'preview.gif');duration=0
   for j in range(gif.n_frames):gif.seek(j);duration+=gif.info['duration']
   assert duration==10*round(len(indexed)*100/30)
  sheet=Image.new('RGBA',(128*6,128*((len(frames)+5)//6)))
  for j,im in enumerate(frames):sheet.paste(im,((j%6)*128,(j//6)*128))
  sheet.save(dest/'sheet.png')
 for mode in modes:
  assert all(np.array_equal(a,b) for a,b in zip(alphas['fixed'],alphas[mode])), 'Mode changed silhouette!'
 stats={}
 for mode in modes:
  counts=[];one_frame=[]
  for j in range(1,len(indices[mode])):
   inside=alphas[mode][j]&alphas[mode][j-1]
   # Screen-space comparison, NOT motion compensated. True motion also counts.
   counts.append(int(np.sum(inside&(indices[mode][j]!=indices[mode][j-1]))))
  for j in range(1,len(indices[mode])-1):
   inside=alphas[mode][j-1]&alphas[mode][j]&alphas[mode][j+1]
   one_frame.append(int(np.sum(inside&(indices[mode][j-1]==indices[mode][j+1])&(indices[mode][j]!=indices[mode][j-1]))))
  stats[mode]={'mean_screen_space_color_changes':float(np.mean(counts)),'mean_single_sample_reversions':float(np.mean(one_frame)),'shadow_pixels_first':int(np.sum(alphas[mode][0]&(indices[mode][0]==1)))}
 report[tag]={'identical_alpha_all_modes':True,'first_frame_height':groups['fixed'][0].getbbox()[3]-groups['fixed'][0].getbbox()[1],'stats':stats}
 all_frames[tag]=groups

def board(groups,index):
 b=Image.new('RGB',(768,420),'#454953');d=ImageDraw.Draw(b)
 for k,mode in enumerate(modes):
  im=groups[mode][index].crop((24,24,104,112)).resize((320,352),Image.Resampling.NEAREST)
  b.paste(im,(k*384+32,44),im);d.text((k*384+18,14),{'dynamic':'A / LIVE NORMAL SHADOW','fixed':'BEFORE / FIXED NORMAL SHADOWS','hybrid':'C / FIXED 85% + LIVE 15%', 'designed':'DESIGNED / ANATOMICAL SHADOWS'}[mode],fill='white')
 return b

for tag, stem in [('pixel-idle','comparison'),('pixel-run','run-comparison')]:
 boards=[board(all_frames[tag],j) for j in range(len(meta[tag]['frames']))]
 durations=[10*(round((j+1)*100/30)-round(j*100/30)) for j in range(len(boards))]
 boards[0].save(O/(stem+'.png'))
 boards[0].save(O/(stem+'.gif'),save_all=True,append_images=boards[1:],duration=durations,loop=0)
 contact=Image.new('RGB',(768,420*4),'#454953')
 for k,j in enumerate(np.linspace(0,len(boards)-1,4,dtype=int)):contact.paste(boards[j],(0,420*k))
 contact.save(O/(stem+'-poses.png'))
report['measurement_note']='30fps source samples, GIF timing rounded to centiseconds. Screen-space changes include motion/occlusion, not a motion-compensated flicker score. Loop seam not validated.'
(O/'pixel-validation.json').write_text(json.dumps(report,indent=2))
print(json.dumps(report,indent=2))

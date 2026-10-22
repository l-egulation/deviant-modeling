from PIL import Image,ImageDraw
from pathlib import Path
import numpy as np,json
R=Path(__file__).resolve().parents[1];O=R/'outputs/hero-art-redesign'
pal=np.array([[int(h[i:i+2],16) for i in (0,2,4)] for h in ['FDEEDA','D2B396','1B1616','025673','02648C','EBA516']],dtype=np.int32)
board=Image.new('RGB',(1536,460),'#505764');d=ImageDraw.Draw(board);report={}
for j,angle in enumerate([None,30,45,60]):
 if angle is None:
  im=Image.open(R/'outputs/art-style-rules/team-native.png').convert('RGBA');tile=Image.new('RGBA',(96,96));tile.alpha_composite(im,(24,16));label='TEAM REFERENCE'
 else:
  tile=Image.open(O/f'view-{angle}.png').convert('RGBA').resize((96,96),Image.Resampling.NEAREST);a=np.array(tile);idx=((a[:,:,:3].astype(np.int32)[:,:,None,:]-pal)**2).sum(3).argmin(2);a[:,:,:3]=pal[idx];a[:,:,3]=np.where(a[:,:,3]>=128,255,0);tile=Image.fromarray(a);tile.save(O/f'pixel-{angle}.png');label=f'3D REDESIGN / {angle} DEG'
  colors=tile.getcolors();report[str(angle)]={'opaque_colors':len({c[:3] for _,c in colors if c[3]}),'alpha':sorted({c[3] for _,c in colors}),'bounds':tile.getbbox()}
 big=tile.resize((384,384),Image.Resampling.NEAREST);board.paste(big,(j*384,55),big);d.text((j*384+15,18),label,fill='white')
board.save(O/'comparison.png');(O/'validation.json').write_text(json.dumps(report,indent=2));print(report)

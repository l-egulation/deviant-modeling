from PIL import Image,ImageDraw
from pathlib import Path
import numpy as np,json
R=Path(__file__).resolve().parents[1];O=R/'outputs/art-style-prototype'
pal=np.array([[int(h[i:i+2],16) for i in (0,2,4)] for h in ['FDEEDA','D2B396','1B1616','025673','02648C','EBA516']],dtype=np.int32)
board=Image.new('RGB',(1440,400),'#535866');d=ImageDraw.Draw(board);report={}
items=[('Team reference',R/'outputs/art-style-rules/team-native.png'),('Original 30 deg',O/'original-30.png'),('Flat side',O/'flat-0.png'),('Flat 30 deg',O/'flat-30.png'),('Flat 45 deg',O/'flat-45.png')]
for j,(label,path) in enumerate(items):
 im=Image.open(path).convert('RGBA')
 if j==0:
  tile=Image.new('RGBA',(96,96));tile.alpha_composite(im,(24,16))
 else:
  tile=im.resize((96,96),Image.Resampling.NEAREST)
  if j>=2:
   a=np.array(tile);idx=((a[:,:,:3].astype(np.int32)[:,:,None,:]-pal)**2).sum(3).argmin(2);a[:,:,:3]=pal[idx];a[:,:,3]=np.where(a[:,:,3]>=128,255,0);tile=Image.fromarray(a)
   tile.save(O/(path.stem+'-native.png'));colors=tile.getcolors();report[label]={'opaque_colors':len({c[:3] for _,c in colors if c[3]}),'alpha_values':sorted({c[3] for _,c in colors}),'bounds':tile.getbbox()}
 board.paste(tile.resize((288,288),Image.Resampling.NEAREST),(j*288,55),tile.resize((288,288),Image.Resampling.NEAREST));d.text((j*288+12,18),label,fill='white')
board.save(O/'comparison.png');(O/'validation.json').write_text(json.dumps(report,indent=2))
print(report)

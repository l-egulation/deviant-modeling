from PIL import Image,ImageDraw
from pathlib import Path
root=Path('.')
sheet=Image.new('RGB',(1536,1056),(238,238,238));d=ImageDraw.Draw(sheet)
labels=['Contact','Support','Push','Flight']
for row,kind in enumerate(['before','after']):
 for col,label in enumerate(labels):
  im=Image.open(root/f'.cache/run-keyposes/{kind}-{col}.png').convert('RGB').resize((384,384),Image.Resampling.LANCZOS)
  x=col*384;y=row*528
  sheet.paste(im,(x,y+32));d.text((x+12,y+10),f'{kind.upper()} / {label}' if row else f'BEFORE / sample {col+1}',fill='black')
  # Extract figure against the known studio background, preserving self-shadow.
  import numpy as np
  a=np.array(im);bg=a[0,0].astype(float);mask=np.linalg.norm(a.astype(float)-bg,axis=2)>30
  silhouette=Image.fromarray((~mask*255).astype('uint8')).resize((96,96),Image.Resampling.NEAREST)
  sheet.paste(silhouette,(x+144,y+420))
sheet.save('outputs/tripo-run-keyposes-comparison.png')

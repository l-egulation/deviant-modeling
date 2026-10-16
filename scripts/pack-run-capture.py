"""Pack raw 30fps transparent captures; no pixel-art conversion yet."""
from pathlib import Path
from PIL import Image,ImageDraw
import json,zipfile
R=Path(__file__).resolve().parents[1];out=R/'outputs/hero-run-capture';meta=json.loads((out/'capture.json').read_text());sheet=Image.new('RGBA',(3072,2048));board=Image.new('RGB',(1536,1024),(65,70,80));draw=ImageDraw.Draw(board);bounds=[]
for i in range(22):
 im=Image.open(out/f'frames/{i:03d}.png').convert('RGBA');assert im.size==(512,512);b=im.getchannel('A').getbbox();assert b and min(b[:2])>0 and max(b[2:])<512,b;bounds.append(b)
 sheet.paste(im,((i%6)*512,(i//6)*512));thumb=im.resize((256,256),Image.Resampling.LANCZOS);board.paste(thumb,((i%6)*256,(i//6)*256),thumb);draw.text(((i%6)*256+8,(i//6)*256+8),f'{i:02d} / {i/30:.3f}s',fill='white')
sheet.save(out/'spritesheet.png');board.save(out/'contact-sheet.png');meta['validation']={'alpha_present':True,'frames_unclipped':True,'alpha_bounds':bounds};(out/'capture.json').write_text(json.dumps(meta,indent=2)+'\n')
with zipfile.ZipFile(R/'outputs/hero-run-capture.zip','w',zipfile.ZIP_DEFLATED) as z:
 for p in sorted(out.rglob('*')):
  if p.is_file():z.write(p,p.relative_to(out))
print(json.dumps({'frame_count':22,'fps':30,'sheet_size':sheet.size,'alpha_and_bounds':'PASS'}))

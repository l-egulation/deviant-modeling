"""Encode the untouched downloaded Mixamo cycle for side-by-side review."""
import av,json,numpy as np
from pathlib import Path
from fractions import Fraction
from PIL import Image,ImageDraw
ROOT=Path(__file__).resolve().parents[1]
report=json.loads((ROOT/'docs/logs/mixamo-running.json').read_text())
count=report['frames'];images=[]
for i in range(count):
    im=Image.new('RGB',(1024,512));d=ImageDraw.Draw(im)
    for col,label in enumerate(('side','three-quarter')):
        im.paste(Image.open(ROOT/f'.cache/mixamo-run/{label}-{i:03d}.png').convert('RGB'),(col*512,0))
    d=ImageDraw.Draw(im);d.text((12,12),'MIXAMO ORIGINAL / SIDE',fill='black');d.text((524,12),'MIXAMO ORIGINAL / THREE-QUARTER',fill='black')
    images.append(im)
dest=ROOT/'outputs/mixamo-running-preview.mp4'
with av.open(str(dest),'w') as c:
    s=c.add_stream('libx264',rate=30);s.width=1024;s.height=512;s.pix_fmt='yuv420p';s.options={'crf':'18'}
    for i,im in enumerate(images*3):
        f=av.VideoFrame.from_ndarray(np.array(im),format='rgb24');f.pts=i;f.time_base=Fraction(1,30)
        for packet in s.encode(f):c.mux(packet)
    for packet in s.encode():c.mux(packet)
with av.open(str(dest)) as c:assert len(list(c.decode(video=0)))==count*3
small=[im.resize((768,384),Image.Resampling.LANCZOS) for im in images]
palette=Image.new('RGB',(768,384*min(6,count)))
for i,im in enumerate(small[::max(1,count//6)][:6]):palette.paste(im,(0,i*384))
palette=palette.quantize(colors=256,method=Image.Quantize.MEDIANCUT)
gif=[im.quantize(palette=palette,dither=Image.Dither.NONE) for im in small]
gif[0].save(ROOT/'outputs/mixamo-running-preview.gif',save_all=True,append_images=gif[1:],duration=([30,30,40]*(count//3+1))[:count],loop=0,optimize=False)
sheet=Image.new('RGB',(1536,1024))
for row,label in enumerate(('side','three-quarter')):
    for col,i in enumerate((0,count//3,count*2//3)):
        sheet.paste(Image.open(ROOT/f'.cache/mixamo-run/{label}-{i:03d}.png').convert('RGB'),(col*512,row*512))
sheet.save(ROOT/'outputs/mixamo-running-contact-sheet.png')
report.update(preview_decoded_frames=count*3,preview_fps=30,preview_seconds=count*3/30,cycle_seconds=count/30,
              note='Preview repeats the downloaded cycle three times; no pose, speed or character retarget edits')
(ROOT/'docs/logs/mixamo-running.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report))

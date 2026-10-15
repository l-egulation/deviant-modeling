"""Encode the rendered 3-second Tripo/Kimodo run and verify decoding."""
import av
import json
import numpy as np
from pathlib import Path
from fractions import Fraction
from PIL import Image,ImageDraw
ROOT=Path(__file__).resolve().parents[1]
frames=[Image.open(ROOT/f'.cache/tripo-run-frames/{f:03d}.png').convert('RGB') for f in range(1,91)]
path=ROOT/'outputs/tripo-run-preview.mp4'
with av.open(str(path),'w') as container:
    stream=container.add_stream('libx264',rate=30);stream.width=stream.height=512;stream.pix_fmt='yuv420p';stream.options={'crf':'18'}
    for i,im in enumerate(frames):
        f=av.VideoFrame.from_ndarray(np.array(im),format='rgb24');f.pts=i;f.time_base=Fraction(1,30)
        for packet in stream.encode(f):container.mux(packet)
    for packet in stream.encode():container.mux(packet)
with av.open(str(path)) as container:
    decoded=list(container.decode(video=0));fps=float(container.streams.video[0].average_rate)
assert len(decoded)==90 and fps==30
small=[im.resize((384,384),Image.Resampling.LANCZOS) for im in frames]
palette=Image.new('RGB',(384*3,384*3))
for i,im in enumerate(small[::10]):palette.paste(im,((i%3)*384,(i//3)*384))
palette=palette.quantize(colors=256,method=Image.Quantize.MEDIANCUT)
gif=[im.quantize(palette=palette,dither=Image.Dither.NONE) for im in small]
gif[0].save(ROOT/'outputs/tripo-run-preview.gif',save_all=True,append_images=gif[1:],duration=[30,30,40]*30,loop=0,optimize=False,disposal=2)
sheet=Image.new('RGB',(1536,1024));draw=ImageDraw.Draw(sheet)
for row,label in enumerate(('front','side')):
    for col,f in enumerate((8,16,32)):
        im=Image.open(ROOT/f'.cache/tripo-run-{label}-{f:03d}.png').convert('RGB')
        sheet.paste(im,(col*512,row*512));draw.text((col*512+12,row*512+12),f'{label} / {f}',fill='black')
sheet.save(ROOT/'outputs/tripo-run-contact-sheet.png')
report={'decoded_frames':len(decoded),'fps':fps,'seconds':3,'motion_source':'Authored 0.6-second cycle from approved pose study on the Kimodo-fitted rig; five repeats',
        'scope':'Video encoding PASS, artistic acceptance and clothing polish are separate'}
(ROOT/'docs/logs/tripo-run-preview.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report))

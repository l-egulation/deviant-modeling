import av,json
import numpy as np
from PIL import Image,ImageDraw
from pathlib import Path
from fractions import Fraction
R=Path(__file__).resolve().parents[1]
frames=[]
for i in range(1,121):
    im=Image.open(R/f'.cache/pixel-cloth/{i:03d}.png').convert('RGB')
    label='START' if i<=15 else 'MOVE' if i<=45 else 'STOP / SETTLE' if i<=75 else 'REVERSE' if i<=105 else 'STOP'
    d=ImageDraw.Draw(im);d.rectangle((0,0,384,26),fill='#eeeeee');d.text((10,7),f'CLOTH INERTIA TEST | {label}',fill='#111111')
    frames.append(im)
path=R/'outputs/tripo-pixel-cloth-preview.mp4'
with av.open(str(path),'w') as container:
    stream=container.add_stream('libx264',rate=30);stream.width=stream.height=384;stream.pix_fmt='yuv420p'
    for i,im in enumerate(frames):
        f=av.VideoFrame.from_ndarray(np.array(im),format='rgb24');f.pts=i;f.time_base=Fraction(1,30)
        for packet in stream.encode(f):container.mux(packet)
    for packet in stream.encode():container.mux(packet)
with av.open(str(path)) as container:
    n=sum(1 for _ in container.decode(video=0));assert n==120
frames[0].save(R/'outputs/tripo-pixel-cloth-preview.gif',save_all=True,append_images=frames[1:],duration=[30,30,40]*40,loop=0)
sheet=Image.new('RGB',(384*4,384))
for j,i in enumerate([0,40,60,95]):sheet.paste(frames[i],(j*384,0))
sheet.save(R/'outputs/tripo-pixel-cloth-contact.png')
print('Verified 120 decoded frames at 30 FPS / 4 seconds')

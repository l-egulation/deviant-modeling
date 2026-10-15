"""Create the rebuild contact sheet and decode-check its joint-test video."""
import json,av,numpy as np
from fractions import Fraction
from pathlib import Path
from PIL import Image,ImageDraw
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'outputs';D=ROOT/'.cache/hero-model-frames'
Image.open(ROOT/'.cache/hero-model-front.png').save(OUT/'hero-model-front.png')
sheet=Image.new('RGB',(1536,1024),(40,44,50));draw=ImageDraw.Draw(sheet)
for i,(name,label) in enumerate((('front','T arms / spread legs / front'),('three-quarter','Rebuilt coat and joint loops'),('side','Neutral / side'))):
    im=Image.open(ROOT/f'.cache/hero-model-{name}.png').convert('RGB').resize((512,512),Image.Resampling.LANCZOS);sheet.paste(im,(i*512,0));draw.text((i*512+12,12),label,fill='white')
for i,f in enumerate((20,60,100)):
    sheet.paste(Image.open(D/f'{f:03d}.png').convert('RGB'),(i*512,512));draw.text((i*512+12,524),f'Joint test / frame {f}',fill='white')
sheet.save(OUT/'hero-model-contact-sheet.png')
dest=OUT/'hero-model-deformation-preview.mp4'
with av.open(str(dest),'w') as c:
    stream=c.add_stream('libx264',rate=30);stream.width=stream.height=512;stream.pix_fmt='yuv420p';stream.options={'crf':'18'}
    for i in range(120):
        frame=av.VideoFrame.from_ndarray(np.array(Image.open(D/f'{i+1:03d}.png').convert('RGB')),format='rgb24');frame.pts=i;frame.time_base=Fraction(1,30)
        for packet in stream.encode(frame):c.mux(packet)
    for packet in stream.encode():c.mux(packet)
with av.open(str(dest)) as c:
    fps=float(c.streams.video[0].average_rate);frames=[f.to_ndarray(format='rgb24') for f in c.decode(video=0)]
motion=float(np.abs(frames[0].astype(float)-frames[60].astype(float)).mean())
assert len(frames)==120 and fps==30 and motion>1
report={'status':'PASS','frames':120,'fps':fps,'seconds':4,'pixel_motion_difference':motion,'scope':'Independent joint-test playback, not generated running motion.'}
preview=[Image.fromarray(frame).resize((384,384),Image.Resampling.LANCZOS) for frame in frames]
training=Image.new('RGB',(384*3,384*3))
for i,frame in enumerate(preview[::15][:9]):training.paste(frame,((i%3)*384,(i//3)*384))
palette=training.quantize(colors=256,method=Image.Quantize.MEDIANCUT)
gif=[im.quantize(palette=palette,dither=Image.Dither.NONE) for im in preview]
gif[0].save(OUT/'hero-model-deformation-preview.gif',save_all=True,append_images=gif[1:],duration=[30,30,40]*40,loop=0,optimize=False,disposal=2)
with Image.open(OUT/'hero-model-deformation-preview.gif') as im:
    total_ms=0
    for i in range(im.n_frames):im.seek(i);total_ms+=im.info['duration']
    assert im.n_frames==120 and total_ms==4000
report.update(gif_frames=120,gif_duration_ms=total_ms)
(ROOT/'docs/logs/hero-model-preview-check.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))

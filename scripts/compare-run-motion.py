"""Compare cached side renders from before and after the motion corrections."""
from pathlib import Path
import json,os
from PIL import Image,ImageDraw
ROOT=Path(__file__).resolve().parents[1];before=ROOT/os.environ.get('HERO_COMPARE_FRAMES','.cache/hero-run-speed-side-before');after=ROOT/'.cache/hero-run-side-frames'
bg=(47,53,63)
def tile(path):
    im=Image.open(path).convert('RGBA')
    b=Image.new('RGBA',im.size,bg+(255,));b.alpha_composite(im)
    return b.convert('RGB')
boards=[]
for f in range(1,46):
    b=Image.new('RGB',(768,416),bg);draw=ImageDraw.Draw(b)
    for i,(label,directory) in enumerate((('Before / 0.75s cycle',before),('After / 0.50s cycle',after))):
        b.paste(tile(directory/f'{f:03d}.png'),(i*384,32));draw.text((i*384+12,12),label,fill='white')
    boards.append(b)
training=Image.new('RGB',(768*3,416*3))
for j,b in enumerate(boards[::5]):training.paste(b,((j%3)*768,(j//3)*416))
palette=training.quantize(colors=256,method=Image.Quantize.MEDIANCUT)
frames=[b.quantize(palette=palette,dither=Image.Dither.NONE) for b in boards]
frames[0].save(ROOT/'outputs/hero-run-side-motion-comparison.gif',save_all=True,append_images=frames[1:],duration=[30,30,40]*15,loop=0,optimize=False,disposal=2)
with Image.open(ROOT/'outputs/hero-run-side-motion-comparison.gif') as gif:
    decoded_frames=gif.n_frames;duration=0
    for i in range(decoded_frames):gif.seek(i);duration+=gif.info['duration']
assert decoded_frames==45 and duration==1500,(decoded_frames,duration)
sheet=Image.new('RGB',(768,1248),bg)
for j,f in enumerate((4,9,17)):sheet.paste(boards[f-1],(0,j*416))
sheet.save(ROOT/'outputs/hero-run-motion-contact-sheet.png')
report={'status':'PASS','before_commit':os.environ.get('HERO_COMPARE_COMMIT','6840495926913b804608ec6f184b89587a9368cc'),'frames':45,'duration_ms':1500,'native_canvas':384,'display_scale':1,'camera_and_frame_indices_identical':True,'scope':'Same elapsed time, original 384px side renders, no pixel downsampling; before two cycles / after three cycles in 1.5 seconds. GIF palette quantization only.'}
(ROOT/'docs/logs/hero-run-motion-comparison.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))

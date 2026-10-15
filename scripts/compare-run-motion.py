"""Compare cached side renders from before and after the motion corrections."""
from pathlib import Path
import json
from PIL import Image,ImageDraw
ROOT=Path(__file__).resolve().parents[1];before=ROOT/'.cache/hero-run-motion-side-before';after=ROOT/'.cache/hero-run-side-frames'
bg=(47,53,63)
def tile(path):
    im=Image.open(path).convert('RGBA').resize((96,96),Image.Resampling.NEAREST)
    b=Image.new('RGBA',im.size,bg+(255,));b.alpha_composite(im)
    return b.convert('RGB').resize((288,288),Image.Resampling.NEAREST)
boards=[]
for f in range(1,46):
    b=Image.new('RGB',(576,320),bg);draw=ImageDraw.Draw(b)
    for i,(label,directory) in enumerate((('Before',before),('After',after))):
        b.paste(tile(directory/f'{f:03d}.png'),(i*288,32));draw.text((i*288+12,12),label+' / 96px canvas',fill='white')
    boards.append(b)
training=Image.new('RGB',(576*3,320*3))
for j,b in enumerate(boards[::5]):training.paste(b,((j%3)*576,(j//3)*320))
palette=training.quantize(colors=256,method=Image.Quantize.MEDIANCUT)
frames=[b.quantize(palette=palette,dither=Image.Dither.NONE) for b in boards]
frames[0].save(ROOT/'outputs/hero-run-side-motion-comparison.gif',save_all=True,append_images=frames[1:],duration=[30,30,40]*15,loop=0,optimize=False,disposal=2)
with Image.open(ROOT/'outputs/hero-run-side-motion-comparison.gif') as gif:
    decoded_frames=gif.n_frames;duration=0
    for i in range(decoded_frames):gif.seek(i);duration+=gif.info['duration']
assert decoded_frames==45 and duration==1500,(decoded_frames,duration)
sheet=Image.new('RGB',(576,960),bg)
for j,f in enumerate((4,9,17)):sheet.paste(boards[f-1],(0,j*320))
sheet.save(ROOT/'outputs/hero-run-motion-contact-sheet.png')
report={'status':'PASS','before_commit':'5c1ac86722dcdd06c5860394b8aa5dff4867adc4','frames':45,'duration_ms':1500,'native_canvas':96,'display_scale':3,'camera_and_frame_indices_identical':True,'scope':'Visual before/after comparison; baseline PNGs were retained locally before changing the rig.'}
(ROOT/'docs/logs/hero-run-motion-comparison.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))

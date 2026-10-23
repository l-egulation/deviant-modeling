"""Package source and cloth comparison without changing animation timing."""
from pathlib import Path
from PIL import Image,ImageDraw,ImageOps
import av,numpy as np,json
R=Path(__file__).resolve().parents[1]
source=Image.open(R/'outputs/pixel-run-candidates.gif')
frames=[]
for i,path in enumerate(sorted((R/'.cache/pixel-run-preview').glob('*.png'))):
 source.seek(i)
 board=Image.new('RGB',(768,416),'#20252c')
 raw=source.convert('RGB').crop((0,0,384,384))
 raw.paste(ImageOps.mirror(raw.crop((0,30,384,384))),(0,30))
 board.paste(raw,(0,32))
 board.paste(Image.open(path).convert('RGB').resize((384,384)),(384,32))
 d=ImageDraw.Draw(board);d.text((10,10),'KIMODO SOURCE / VIEW MIRRORED',fill='white');d.text((394,10),'FITTED RIG + CLOTH / TEST',fill='white');frames.append(board)
assert len(frames)==90
with av.open(str(R/'outputs/pixel-run-comparison.mp4'),'w') as out:
 stream=out.add_stream('libx264',rate=30);stream.width=768;stream.height=416;stream.pix_fmt='yuv420p';stream.options={'crf':'19'}
 for im in frames:
  for packet in stream.encode(av.VideoFrame.from_ndarray(np.asarray(im),format='rgb24')):out.mux(packet)
 for packet in stream.encode():out.mux(packet)
frames[0].save(R/'outputs/pixel-run-comparison.gif',save_all=True,append_images=frames[1:],duration=[30,30,40]*30,loop=0)
sheet=Image.new('RGB',(1152,1248),'#20252c')
for i,f in enumerate(range(0,90,10)):
 tile=frames[f].crop((384,0,768,416));ImageDraw.Draw(tile).text((10,32),f'FRAME {f+1}',fill='white');sheet.paste(tile,((i%3)*384,(i//3)*416))
sheet.save(R/'outputs/pixel-run-contact-sheet.png')
with av.open(str(R/'outputs/pixel-run-comparison.mp4')) as check:
 count=sum(1 for _ in check.decode(video=0));assert count==90
gif=Image.open(R/'outputs/pixel-run-comparison.gif');assert gif.n_frames==90
duration=0
for f in range(gif.n_frames):gif.seek(f);duration+=gif.info['duration']
assert duration==3000
(R/'docs/logs/pixel-run-media.json').write_text(json.dumps({'decoded_frames':count,'fps':30,'seconds':3,'gif_frames':gif.n_frames,'gif_duration_ms':duration,'loop_seam_verified':False},indent=2))

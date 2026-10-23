"""Annotate rendered evidence and encode the diagnostic preview."""
from pathlib import Path
from PIL import Image,ImageDraw
import json, av, numpy as np
R=Path(__file__).resolve().parents[1]
d=json.loads((R/'docs/logs/pixel-rig.json').read_text())
board=Image.new('RGB',(1024,556),'#20252c')
for col,label in enumerate(['front','side']):
 im=Image.open(R/f'outputs/tripo-pixel-rig-{label}.png').convert('RGB');draw=ImageDraw.Draw(im)
 for name,(a,b) in d['projections'][label].items():
  color='#ffbe48' if '.L' in name else '#62e0fc' if '.R' in name else '#f15b8a'
  draw.line([tuple(a),tuple(b)],fill=color,width=3)
  for x,y in [a,b]:draw.ellipse((x-3,y-3,x+3,y+3),fill=color,outline='#202020')
 board.paste(im,(col*512,36))
ImageDraw.Draw(board).text((16,12),'CHARACTER-FITTED RIG / FRONT + SIDE / FIXED BONE LENGTHS',fill='white')
board.save(R/'outputs/tripo-pixel-rig-overview.png')
poses=Image.new('RGB',(1536,548),'#20252c');draw=ImageDraw.Draw(poses)
for i,(f,label) in enumerate([(21,'SHOULDER / ELBOW'),(41,'KNEE'),(61,'TORSO')]):
 poses.paste(Image.open(R/f'outputs/tripo-pixel-rig-test-{f}.png').convert('RGB'),(i*512,36));draw.text((i*512+16,12),label+' - JOINT TEST, NOT RUNNING',fill='white')
poses.save(R/'outputs/tripo-pixel-rig-joint-tests.png')
frames=[]
with av.open(str(R/'outputs/tripo-pixel-rig-preview.mp4'),'w') as out:
 stream=out.add_stream('libx264',rate=30);stream.width=384;stream.height=416;stream.pix_fmt='yuv420p';stream.options={'crf':'20'}
 for path in sorted((R/'.cache/pixel-rig').glob('*.png')):
  im=Image.new('RGB',(384,416),'#20252c');im.paste(Image.open(path).convert('RGB'),(0,32));ImageDraw.Draw(im).text((10,10),'JOINT TEST / NOT KIMODO RUNNING',fill='white');frames.append(im)
  frame=av.VideoFrame.from_ndarray(np.asarray(im),format='rgb24')
  for packet in stream.encode(frame):out.mux(packet)
 for packet in stream.encode():out.mux(packet)
frames[0].save(R/'outputs/tripo-pixel-rig-preview.gif',save_all=True,append_images=frames[1:],duration=[30 if (i+1)%3 else 40 for i in range(len(frames))],loop=0)
print('Packaged',len(frames),'frames')
with av.open(str(R/'outputs/tripo-pixel-rig-preview.mp4')) as check:
 decoded=list(check.decode(video=0));fps=float(check.streams.video[0].average_rate)
 assert len(decoded)==d['test_frames'] and fps==30
gif=Image.open(R/'outputs/tripo-pixel-rig-preview.gif');duration=0
for i in range(gif.n_frames):gif.seek(i);duration+=gif.info.get('duration',0)
assert gif.n_frames==d['test_frames']
(R/'docs/logs/pixel-rig-media.json').write_text(json.dumps({'mp4_decoded_frames':len(decoded),'fps':fps,'gif_frames':gif.n_frames,'gif_duration_ms':duration},indent=2))

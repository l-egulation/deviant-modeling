"""Encode side playback and fixed-palette small-resolution comparisons."""
from pathlib import Path
import json
from fractions import Fraction
import av,numpy as np
from PIL import Image,ImageDraw
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'outputs';D=ROOT/'.cache/hero-run-side-frames'
source=[Image.open(D/f'{i:03d}.png').convert('RGBA') for i in range(1,46)]
bg=(47,53,63);sizes=(128,96,64)
def matte(im):
    canvas=Image.new('RGBA',im.size,bg+(255,));canvas.alpha_composite(im);return canvas.convert('RGB')
boards=[]
for im in source:
    board=Image.new('RGB',(768,576),bg);draw=ImageDraw.Draw(board)
    for j,n in enumerate(sizes):
        low=im.resize((n,n),Image.Resampling.NEAREST)
        color=matte(low).resize((256,256),Image.Resampling.NEAREST)
        silhouette=Image.new('RGB',(n,n),bg);mask=low.getchannel('A').point(lambda a:255 if a>=128 else 0)
        silhouette.paste((230,235,240),(0,0,n,n),mask)
        board.paste(color,(j*256,32));board.paste(silhouette.resize((256,256),Image.Resampling.NEAREST),(j*256,320))
        draw.text((j*256+12,12),f'{n} x {n} canvas / nearest',fill='white')
        draw.text((j*256+12,300),'Silhouette',fill='white')
    boards.append(board)
training=Image.new('RGB',(768*3,576*3))
for j,im in enumerate(boards[::5]):training.paste(im,((j%3)*768,(j//3)*576))
palette=training.quantize(colors=256,method=Image.Quantize.MEDIANCUT)
gif=[b.quantize(palette=palette,dither=Image.Dither.NONE) for b in boards]
gif[0].save(OUT/'hero-run-side-scale-comparison.gif',save_all=True,append_images=gif[1:],duration=[30,30,40]*15,loop=0,optimize=False,disposal=2)
with av.open(str(OUT/'hero-run-side-preview.mp4'),'w') as c:
    stream=c.add_stream('libx264',rate=30);stream.width=stream.height=384;stream.pix_fmt='yuv420p';stream.options={'crf':'18'}
    for i in range(90):
        frame=av.VideoFrame.from_ndarray(np.array(matte(source[i%45])),format='rgb24');frame.pts=i;frame.time_base=Fraction(1,30)
        for packet in stream.encode(frame):c.mux(packet)
    for packet in stream.encode():c.mux(packet)
sheet=Image.new('RGB',(768,560),bg)
for j,f in enumerate((1,5,9,13,17,21)):
    tile=matte(source[f-1].resize((96,96),Image.Resampling.NEAREST)).resize((256,256),Image.Resampling.NEAREST)
    x=(j%3)*256;y=(j//3)*280;sheet.paste(tile,(x,y+24));ImageDraw.Draw(sheet).text((x+8,y+8),f'frame {f} / 96px canvas',fill='white')
sheet.save(OUT/'hero-run-side-contact-sheet.png')
first=np.array(source[0],dtype=float);end=np.array(Image.open(D/'046.png').convert('RGBA'),dtype=float)
loop_error=float(np.abs(first-end).mean());assert loop_error<1,loop_error
bounds=np.array([im.getbbox() for im in source]);assert (bounds[:,:2]>5).all() and (bounds[:,2:]<379).all()
with av.open(str(OUT/'hero-run-side-preview.mp4')) as c:
    fps=float(c.streams.video[0].average_rate);frames=sum(1 for _ in c.decode(video=0))
assert fps==30 and frames==90
with Image.open(OUT/'hero-run-side-scale-comparison.gif') as im:
    gif_ms=0;gif_frames=im.n_frames
    for i in range(gif_frames):im.seek(i);gif_ms+=im.info['duration']
assert gif_ms==1500
report={'status':'PASS','camera':'Fixed orthographic, pure side, no elevation','linear_root_travel_removed':True,'source_blend_file_modified':False,'preview_object_translation_rebased':True,'rendered_frames':45,'endpoint_frame':46,'render_size':[384,384],'clip_seconds':1.5,'mp4_frames':frames,'mp4_fps':fps,'mp4_seconds':3,'gif_frames':gif_frames,'gif_duration_ms':gif_ms,'loop_endpoint_rgba_mean_difference':loop_error,'alpha_bounds_min':bounds.min(0).tolist(),'alpha_bounds_max':bounds.max(0).tolist(),'canvas_sizes':list(sizes),'character_pixel_height_ranges':{str(n):[float((bounds[:,3]-bounds[:,1]).min()*n/384),float((bounds[:,3]-bounds[:,1]).max()*n/384)] for n in sizes},'scope':'Nearest-neighbor reduction and silhouette review. No AI stylization or per-frame repaint. Numeric PASS covers encoding, framing and loop only; artistic quality needs visual review.'}
(ROOT/'docs/logs/hero-run-side-check.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))

#!/usr/bin/env python3
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
import subprocess,json,math,numpy as np
ROOT=Path(__file__).resolve().parents[1];V=ROOT/'kick_rank_drama.mp4';P=ROOT/'preview'
def cmd(args):return subprocess.run(args,capture_output=True,text=True)
def main():
 T=json.loads((ROOT/'timings.json').read_text());S=json.loads((ROOT/'shots.json').read_text())
 meta=cmd(['ffmpeg','-hide_banner','-i',str(V)]).stderr;(P/'media_info.txt').write_text(meta)
 stats=cmd(['ffmpeg','-hide_banner','-i',str(V),'-vn','-af','astats=metadata=0:reset=0','-f','null','-']).stderr;(P/'final_audio_stats.txt').write_text(stats)
 assert '1280x720' in meta and '30 fps' in meta and 'stereo' in meta
 for i,s in enumerate(S):
  if i:assert abs(s['start']-(S[i-1]['start']+S[i-1]['dur']))<.04
 assert abs(sum(s['dur'] for s in S)-T['total'])<.04
 f=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',16)
 for k in range(math.ceil(len(S)/20)):
  canvas=Image.new('RGB',(1280,5*205),'#090d10');d=ImageDraw.Draw(canvas)
  for j,s in enumerate(S[k*20:(k+1)*20]):
   t=s['start']+min(s['dur']*.55,2.6)
   frame=P/f"final_{s['id']}.jpg"
   subprocess.run(['ffmpeg','-v','error','-y','-ss',str(t),'-i',str(V),'-frames:v','1',str(frame)],check=True)
   x=j%4*320;y=j//4*205;canvas.paste(Image.open(frame).resize((320,180)),(x,y));d.text((x+5,y+182),f"{s['id']} | {t:.2f}s",font=f,fill='white')
  canvas.save(P/f'QA_FINAL_{k+1}.jpg',quality=93)
 report={'duration_seconds':T['total'],'resolution':'1280x720','fps':30,'audio':'AAC 44100 Hz stereo','shots':len(S),'max_shot_seconds':max(s['dur'] for s in S),'timeline_contiguous':True,'caption_method':'Whisper word timestamps aligned to reference; clip C2 phrase timings manually corrected','checks':'See QA_FINAL_1–3.jpg and final_audio_stats.txt. Visual review required.'}
 (P/'qa_report.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2))
if __name__=='__main__':main()

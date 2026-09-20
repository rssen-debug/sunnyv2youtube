#!/usr/bin/env python3
"""720p/30 documentary renderer adapted from repo pipeline.
Per-shot renders reduce filtergraph memory. Keeps zoom/ease, captions, real clips,
original audio, impacts, risers and ducking. Source video/audio use IDENTICAL cuts.
"""
from pathlib import Path
import subprocess,json,math,wave,concurrent.futures
import numpy as np
ROOT=Path(__file__).resolve().parents[1]
CACHE=ROOT/'.cache/render';CACHE.mkdir(parents=True,exist_ok=True)
GFX=ROOT/'assets/gfx';AUDIO=ROOT/'audio';CLIPDIR=ROOT/'assets/clips'
FPS=30;RATE=44100
T=json.loads((ROOT/'timings.json').read_text());SHOTS=json.loads((ROOT/'shots.json').read_text());TOTAL=T['total']

def run(cmd,log):
 with open(log,'w') as f:
  p=subprocess.run(cmd,stdout=f,stderr=f)
 if p.returncode:raise RuntimeError(Path(log).read_text()[-5000:])

def render(s):
 out=CACHE/(s['id']+'.mp4');nf=round(s['dur']*FPS)
 if out.exists() and out.stat().st_size>1000:return out
 cmd=['ffmpeg','-y','-v','error','-threads','1','-filter_complex_threads','1','-framerate','30','-i',str(GFX/s['image'])]
 if s['kind']=='still':
  # Smoothstep 'F9' entrance on a restrained Ken Burns push/pull.
  z0=1.037 if s['variant'] else 1.0
  z=f'{z0}+0.027*on/{max(1,nf-1)}'
  vf=f"scale=1920:1080,zoompan=z='{z}':x='iw/2-(iw/zoom)/2':y='ih/2-(ih/zoom)/2':d={nf}:s=1280x720:fps=30,setsar=1"
  # Brief motivated exposure dip on big chapter changes, not continuous flashes.
  if s['id'] in ['A3_00_0','A4_00_0','B2_00_0']:vf+=',fade=t=in:st=0:d=0.13'
  cmd+=['-vf',vf]
 else:
  cmd+=['-ss',str(s['cut']),'-t',str(s['dur']),'-i',str(CLIPDIR/s['file'])]
  crop='crop=1152:648:64:36,' if s['variant'] else ''
  # Source frame remains above caption-safe y=570.
  fg=f"[0:v]loop=loop=-1:size=1:start=0,setpts=N/30/TB[base];[1:v]{crop}fps=30,scale=750:422,setsar=1,setpts=PTS-STARTPTS,drawbox=x=0:y=0:w=iw:h=ih:color=white@0.4:t=2[v];[base][v]overlay=x=265:y=140:shortest=1[out]"
  cmd+=['-filter_complex',fg,'-map','[out]']
 if s['id']=='END':cmd+=['-vf',"fade=t=out:st=1.5:d=1.0"] if s['kind']!='still' else []
 cmd+=['-frames:v',str(nf),'-an','-c:v','libx264','-preset','veryfast','-crf','21','-pix_fmt','yuv420p','-r','30','-video_track_timescale','15360','-threads','1',str(out)]
 run(cmd,CACHE/(s['id']+'.log'));print('Rendered',s['id'],flush=True);return out

def decoded(path,cut=None,dur=None):
 cmd=['ffmpeg','-v','error']
 if cut is not None:cmd+=['-ss',str(cut)]
 cmd+=['-i',str(path)]
 if dur is not None:cmd+=['-t',str(dur)]
 cmd+=['-vn','-ac','1','-ar',str(RATE),'-f','f32le','-']
 p=subprocess.run(cmd,capture_output=True,check=True);return np.frombuffer(p.stdout,dtype=np.float32).copy()

def make_audio():
 n=round(TOTAL*RATE);t=np.arange(n,dtype=np.float32)/RATE
 bed=(.008*np.sin(2*np.pi*49*t)+.005*np.sin(2*np.pi*49.5*t)+.003*np.sin(2*np.pi*98*t)+.003*np.sin(2*np.pi*196.8*t)*(.5+.5*np.sin(2*np.pi*.1*t)))
 voice=np.zeros(n,dtype=np.float32);fx=np.zeros(n,dtype=np.float32);measure=[]
 def add(dst,x,start):
  a=max(0,round(start*RATE));b=min(n,a+len(x));dst[a:b]+=x[:b-a]
 for s in T['segments']:
  if s['kind']=='end':continue
  if s['kind']=='clip':
   x=decoded(CLIPDIR/s['file'],s['cut'],s['dur']);target=.117
   a=round(s['start']*RATE);b=round((s['start']+s['dur'])*RATE);bed[a:b]*=.17
  else:x=decoded(AUDIO/(s['id']+'.wav'));target=.105
  rms=float(np.sqrt(np.mean(x*x)));gain=target/max(rms,1e-6);x*=gain
  # Preserve clear dialogue and keep source clip volume at least .75.
  if s['kind']=='clip' and gain<.75:x*=.75/gain;gain=.75
  # Fade only the first/last 8ms to avoid clicks.
  m=min(352,len(x)//2);x[:m]*=np.linspace(0,1,m);x[-m:]*=np.linspace(1,0,m)
  add(voice,x,s['start']);measure.append({'id':s['id'],'source_rms':rms,'gain':gain,'mixed_voice_rms':float(np.sqrt(np.mean(x*x)))})
 # Synthetically composed impacts and whooshes, no external music samples.
 for i,s in enumerate(SHOTS):
  if s['id']=='END':continue
  tt=np.arange(round(.27*RATE))/RATE
  rng=np.random.default_rng(i+17);noise=rng.normal(0,1,len(tt));noise=np.convolve(noise,np.ones(11)/11,mode='same')
  whoosh=.027*noise*np.sin(np.pi*tt/.27)**2
  add(fx,whoosh,max(0,s['start']-.16))
 for id in ['A1','A3','A4','B1','B2','A6']:
  s=next(x for x in T['segments'] if x['id']==id);at=s['start'];tt=np.arange(round(1.1*RATE))/RATE
  boom=.11*np.sin(2*np.pi*52*tt)*np.exp(-7*tt)+.035*np.sin(2*np.pi*110*tt)*np.exp(-11*tt);add(fx,boom,at)
  if at>3:
   tt=np.arange(round(1.6*RATE))/RATE
   riser=.012*np.sin(2*np.pi*(160+70*tt)*tt)*(tt/1.6)**2
   add(fx,riser,at-1.8)
 # Intentional half-second bed drop before apology; narration remains fully audible.
 a=round((next(s for s in T['segments'] if s['id']=='B2')['start']-.5)*RATE);bed[a:a+round(.65*RATE)]=0
 mono=voice+bed+fx
 # Soft-knee peak control: do not attenuate the entire film for one source transient.
 mono=.68*np.tanh(mono/.68)
 # Stereo ambience, centre dialogue; final fade removes drone tail cleanly.
 left=mono.copy();right=mono.copy();right+=.0015*np.sin(2*np.pi*73.42*t)
 fade=np.ones(n,dtype=np.float32);fade[-RATE:]=np.linspace(1,0,RATE);left*=fade;right*=fade
 stereo=np.stack([left,right],axis=1);stereo=np.clip(stereo,-.89,.89)
 with wave.open(str(CACHE/'mix.wav'),'wb') as w:
  w.setnchannels(2);w.setsampwidth(2);w.setframerate(RATE);w.writeframes((stereo*32767).astype('<i2').tobytes())
 report={'segments':measure,'peak_dbfs':20*math.log10(float(np.max(np.abs(stereo)))+1e-12),'rms_dbfs':20*math.log10(float(np.sqrt(np.mean(stereo*stereo)))+1e-12),'clip_windows':[]}
 for s in T['segments']:
  if s['kind']=='clip':
   a=round(s['start']*RATE);b=round((s['start']+s['dur'])*RATE)
   report['clip_windows'].append({'id':s['id'],'dialogue_rms':float(np.sqrt(np.mean(voice[a:b]**2))),'drone_rms':float(np.sqrt(np.mean(bed[a:b]**2)))})
 (ROOT/'preview/audio_qa.json').write_text(json.dumps(report,indent=2));print('Audio',report['peak_dbfs'],report['rms_dbfs'],flush=True)

def main():
 make_audio()
 with concurrent.futures.ThreadPoolExecutor(max_workers=2) as ex:list(ex.map(render,SHOTS))
 (CACHE/'concat.txt').write_text('\n'.join("file '"+str(CACHE/(s['id']+'.mp4'))+"'" for s in SHOTS))
 run(['ffmpeg','-v','error','-y','-f','concat','-safe','0','-i',str(CACHE/'concat.txt'),'-c','copy',str(CACHE/'visuals.mp4')],CACHE/'concat.log')
 vf=f"ass={ROOT/'captions.ass'},fade=t=out:st={TOTAL-1:.3f}:d=1"
 run(['ffmpeg','-v','error','-y','-threads','2','-i',str(CACHE/'visuals.mp4'),'-i',str(CACHE/'mix.wav'),'-vf',vf,'-map','0:v','-map','1:a','-c:v','libx264','-preset','veryfast','-crf','22','-threads','2','-pix_fmt','yuv420p','-c:a','aac','-b:a','160k','-ar','44100','-ac','2','-t',str(TOTAL),'-movflags','+faststart','-metadata','title=Banned for Friends? The Kick Streamer Rank Dispute',str(ROOT/'kick_rank_drama.mp4')],CACHE/'final.log')
 print('FINAL',ROOT/'kick_rank_drama.mp4',flush=True)
if __name__=='__main__':main()

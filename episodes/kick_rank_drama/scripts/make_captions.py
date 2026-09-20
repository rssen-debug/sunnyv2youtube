#!/usr/bin/env python3
"""Pipeline caption/timing upgrade: reference-text alignment to Whisper word timestamps.
Keeps pop captions, 720p safe zone; reserves un-narrated slots for original clips.
Whisper JSON is cached in audio/; no model download needed for rebuild.
"""
import json,re,wave,math,difflib
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
FPS=30
CLIP_INSERTS={'A2':{'id':'C1','file':'train.mp4','cut':0.25,'dur':10.4,'speaker':'TRAINWRECKSTV','source':'X / @TrainUpdates • original Kick broadcast'},'A4':{'id':'C2','file':'trick.mp4','cut':10.65,'dur':16.75,'speaker':'TRICK2G','source':'X / @Trick2g • public appeal'}}
def norm(s):return re.sub('[^a-z0-9]','',s.lower())
def align(text,asr,dur):
    ref=text.split(); a=[norm(w) for w in ref]; b=[norm(w['word']) for w in asr]
    out=[None]*len(ref)
    for tag,i,j,k,l in difflib.SequenceMatcher(None,a,b,autojunk=False).get_opcodes():
        if tag=='equal':
            for n,m in zip(range(i,j),range(k,l)):out[n]={'word':ref[n],'start':asr[m]['start'],'end':asr[m]['end']}
        elif i<j:
            lo=asr[k]['start'] if k<len(asr) else dur-.15
            hi=asr[l-1]['end'] if l>k else lo+.08*(j-i)
            if k==l and k<len(asr):lo=asr[k-1]['end'] if k else 0;hi=asr[k]['start']
            weights=[len(ref[n])+2 for n in range(i,j)]; tot=sum(weights);acc=lo
            for n,weight in zip(range(i,j),weights):
                end=acc+max(.04,hi-lo)*weight/tot;out[n]={'word':ref[n],'start':acc,'end':end};acc=end
    return out

def ts(t):return f'{int(t//3600)}:{int(t%3600//60):02d}:{t%60:05.2f}'
HEADER='''[Script Info]
ScriptType: v4.00+
PlayResX: 1280
PlayResY: 720
WrapStyle: 2
ScaledBorderAndShadow: yes
[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Pop,DejaVu Sans,45,&H00FFFFFF,&H000000FF,&H00000000,&HA0000000,-1,0,0,0,100,100,0,0,1,3,1,2,50,50,69,1
[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
'''

def make():
    blocks=[]
    for part in (ROOT/'script/script.txt').read_text().split('###')[1:]:
        id,text=part.strip().split('\n',1);blocks.append((id,text.strip()))
    timeline=[];t=0
    for id,text in blocks:
        with wave.open(str(ROOT/f'audio/{id}.wav')) as w:dur=w.getnframes()/w.getframerate()
        words=align(text,json.loads((ROOT/f'audio/{id}_words.json').read_text()),dur)
        seg={'id':id,'text':text,'start':t,'dur':math.ceil((dur+.35)*FPS)/FPS,'vo_dur':dur,'words':words,'kind':'narration'}
        timeline.append(seg);t+=seg['dur']
        if id in CLIP_INSERTS:
            c=CLIP_INSERTS[id].copy();c['dur']=math.ceil(c['dur']*FPS)/FPS;c.update(start=t,kind='clip')
            raw=json.loads((ROOT/f"assets/clips/{c['file'].split('.')[0]}_transcript.json").read_text())
            words=[w.copy() for seg in raw for w in seg['words'] if w['start']>=c['cut'] and w['end']<=c['cut']+c['dur']]
            # Correct recogniser mistakes against source quotations (Sportskeeda / NDTV).
            corrections={'S.O.,':'Yassuo,','Reveal.':'review.','Boston.':'boosting.','Boston':'boosting','Automative.':'Automated','The':'It’s','saying':'saying'}
            for w in words:
                w['word']=w['word'].strip()
                if c['id']=='C1' and w['word']=='S.O.,':w['word']='Yassuo,'
                if c['id']=='C2':
                    w['word']=corrections.get(w['word'],w['word'])
                w['start']-=c['cut'];w['end']-=c['cut']
            if c['id']=='C1':
                words=align("Guys, they banned me on League of Legends for playing with Tyler1, Trick2g, Yassuo, and all these guys on stream. I don't get it. What do they expect me to do?",words,c['dur'])
            if c['id']=='C2':
                phrases=[(10.98,13.34,"It's saying that we're boosting."),(13.88,15.0,'No boosting was happening.'),(16.34,20.24,'What happened was somebody who has never played Flex'),(20.82,21.62,'was too low.'),(21.9,22.68,"We couldn't play with him."),(22.84,24.28,'So me and Cookie'),(25.24,27.24,'and Moe had to switch accounts sometimes.')]
                words=[]
                for a,b,phrase in phrases:
                    ww=phrase.split()
                    for n,word in enumerate(ww):words.append({'word':word,'start':a-c['cut']+(b-a)*n/len(ww),'end':a-c['cut']+(b-a)*(n+1)/len(ww)})
            c['words']=words;timeline.append(c);t+=c['dur']
    # Endcard hold (not narration)
    timeline.append({'id':'END','kind':'end','start':t,'dur':2.5,'words':[]});t+=2.5
    (ROOT/'timings.json').write_text(json.dumps({'segments':timeline,'total':t,'fps':FPS},indent=2))
    events=[];srt=[]
    for s in timeline:
        group=[]
        def flush():
            if not group:return
            a=s['start']+group[0]['start'];b=s['start']+group[-1]['end']
            text=' '.join(w['word'] for w in group)
            fx=r'{\fscx86\fscy86\t(0,65,\fscx100\fscy100)\fad(20,35)}'
            events.append(f'Dialogue: 0,{ts(a)},{ts(max(a+.08,b))},Pop,,0,0,0,,{fx}{text}')
            srt.append((a,b,text))
            group.clear()
        for w in s.get('words',[]):
            if group and (len(group)>=3 or len(' '.join(x['word'] for x in group))+len(w['word'])>22):flush()
            group.append(w)
            if re.search(r'[.!?]$',w['word']):flush()
        flush()
    (ROOT/'captions.ass').write_text(HEADER+'\n'.join(events)+'\n')
    def st(t):return f'{int(t//3600):02d}:{int(t%3600//60):02d}:{int(t%60):02d},{round((t%1)*1000):03d}'
    (ROOT/'captions.srt').write_text('\n\n'.join(f'{i+1}\n{st(a)} --> {st(b)}\n{text}' for i,(a,b,text) in enumerate(srt)))
    print('Timeline:',round(t,2),'seconds;',len(events),'caption groups')
if __name__=='__main__':make()

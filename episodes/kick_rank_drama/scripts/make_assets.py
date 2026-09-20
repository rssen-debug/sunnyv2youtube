#!/usr/bin/env python3
"""Topic-specific Pillow GFX factory, following repository circle/card system.
Editorial quote cards are labelled excerpts, never counterfeit screenshots.
"""
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont,ImageOps,ImageEnhance,ImageFilter
import json,re,math,shutil
ROOT=Path(__file__).resolve().parents[1]; SRC=ROOT/'assets/src'; GFX=ROOT/'assets/gfx'
GFX.mkdir(exist_ok=True)
W,H=1280,720
GREEN='#8aff39'; RED='#ff565f'; WHITE='#f2f4f1'; MUTED='#a9b4be'; GOLD='#e0be78'
FONT='/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'
REG='/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'
MONO='/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf'
def font(s,bold=True):return ImageFont.truetype(FONT if bold else REG,s)
def txt(im,xy,text,size=44,color=WHITE,bold=True):
 d=ImageDraw.Draw(im);d.text(xy,text,font=font(size,bold),fill=color,stroke_width=0)
def wrap(text,size,width):
 d=ImageDraw.Draw(Image.new('RGB',(10,10)));lines=[]
 for para in text.split('\n'):
  line=''
  for word in para.split():
   test=(line+' '+word).strip()
   if d.textlength(test,font=font(size))>width and line:lines.append(line);line=word
   else:line=test
  lines.append(line)
 return lines
def lines(im,xy,text,size=44,color=WHITE,width=1080,step=None,bold=True):
 for i,line in enumerate(wrap(text,size,width)):txt(im,(xy[0],xy[1]+i*(step or int(size*1.2))),line,size,color,bold)
def fit(im,box):return ImageOps.fit(im,(box[2]-box[0],box[3]-box[1]),method=Image.Resampling.LANCZOS)
def circle(im,src,box,color=GREEN):
 p=fit(Image.open(src).convert('RGB'),box);mask=Image.new('L',p.size);ImageDraw.Draw(mask).ellipse((0,0,p.width-1,p.height-1),fill=255)
 im.paste(p,box[:2],mask);ImageDraw.Draw(im).ellipse(box,outline=color,width=4)
def photo(im,src,box):
 p=Image.open(src).convert('RGB');p=ImageOps.contain(p,(box[2]-box[0],box[3]-box[1]),Image.Resampling.LANCZOS)
 x=box[0]+(box[2]-box[0]-p.width)//2;y=box[1]+(box[3]-box[1]-p.height)//2
 im.paste(p,(x,y));ImageDraw.Draw(im).rectangle((x,y,x+p.width,y+p.height),outline='#607469',width=2)
def base(chapter,source):
 im=ImageOps.fit(Image.open(SRC/'bg_ai.png').convert('RGB'),(W,H))
 d=ImageDraw.Draw(im);d.rectangle((0,570,1280,720),fill='#080c10');d.line((54,84,1226,84),fill='#344337',width=1)
 d.rectangle((54,42,63,63),fill=GREEN)
 txt(im,(76,37),'STREAM / FILES',21,GREEN)
 txt(im,(720,40),chapter.upper(),17,MUTED)
 d.line((54,670,1226,670),fill='#29342e',width=1)
 txt(im,(54,682),source,13,MUTED,False)
 txt(im,(1038,682),'20 SEP 2026',13,MUTED,False)
 return im

# Photographs and actual stream screenshots. Archive portraits are always labelled.
if not (SRC/'train_portrait.jpg').exists():
 p=Image.open('/home/user/image-search/trainwreckstv-kick-streamer-headphones-f-1.jpg').convert('RGB')
 p.crop((420,20,1300,882)).save(SRC/'train_portrait.jpg',quality=94)
if not (SRC/'trick_portrait.jpg').exists():
 p=Image.open(SRC/'trick_frame.jpg').convert('RGB');p.crop((0,409,320,720)).save(SRC/'trick_portrait.jpg',quality=94)
 p.crop((636,26,1177,445)).save(SRC/'notice.jpg',quality=95)

# Each cue is anchored to the spoken words, rather than an arbitrary equal split.
# cue, layout, heading, supporting line, image/left/right as applicable.
D={
'A1':[
 ('A Kick','hero','BANNED FOR\nFRIENDS?','TRAINWRECKSTV / THE RANK DISPUTE','train'),
 ('Riot says','title','RIOT PUSHES BACK','RANK MANIPULATION  /  ENFORCEMENT','red'),
 ('Then a public','title','AN APOLOGY.','BUT NOT A POLICY REVERSAL.','green'),
 ('This is','duo','TRAINWRECKS × TRICK2G','SEPTEMBER 2026 / THE DISPUTE',''),
 ('And the detail','flow','NOT JUST WHO.','THE ACCOUNTS MATTER.','FRIENDS|ACCOUNTS|RULES')],
'A2':[
 ('First','compare','LEAGUE BAN','NOT A KICK BAN','RIOT / GAME ACCOUNT|KICK / STREAMING PLATFORM'),
 ('Trainwrecks discussed','photo','THE KICK BROADCAST','STREAM FRAME / SEPTEMBER 2026','train_frame.jpg'),
 ('He said','flow','THE GROUP','TRAINWRECKS’ ACCOUNT OF EVENTS','TYLER1|TRICK2G|YASSUO'),
 ('then found','title','RANK ROLLED BACK','TRAINWRECKS SAYS HE WAS BANNED','red'),
 ('To him','hero','“I DON’T\nGET IT.”','TRAINWRECKS / EXCERPT FROM HIS RESPONSE','train'),
 ('His defence','title','FRIENDS. NOT A SERVICE.','HIS EXPLANATION  →  ORIGINAL AUDIO','green')],
'A3':[
 ('But this','title','BIGGER THAN\nONE STREAMER','A PLATFORM-WIDE ENFORCEMENT STORY','green'),
 ('On September','number','296,416','ACCOUNTS / LEAGUE + VALORANT','RIOT’S REPORTED RUNNING TOTAL'),
 ('accounts penalised','number','296,416','ACCOUNTS / LEAGUE + VALORANT','17 SEPTEMBER / RIOT ANNOUNCEMENT'),
 ('That was','title','A RUNNING TOTAL','NOT A SINGLE NIGHT’S BAN WAVE','green'),
 ('Riot’s message','quote','“Boosting, smurfing,\nhitchhiking… it’s all cheating.”','RIOT GAMES / X / 17 SEPTEMBER','EXCERPT • AS QUOTED BY NDTV'),
 ('The streamers','duo','TWO STREAMERS.','A MUCH WIDER CRACKDOWN.','')],
'A4':[
 ('Then','hero','THE PUBLIC\nAPPEAL','TRICK2G / ORIGINAL APPEAL FRAME','trick'),
 ('He said','flow','TOO LOW TO QUEUE','TRICK2G’S EXPLANATION','FLEX PLACEMENT|RANK GAP|GROUP BLOCKED'),
 ('So some','notice','THE DISPLAYED NOTICE','ACTUAL FRAME FROM TRICK2G’S PUBLIC APPEAL',''),
 ('He denied','quote','“No boosting\nwas happening.”','TRICK2G / PUBLIC APPEAL','EXCERPT • SOURCE CLIP'),
 ('That distinction','compare','PLAYING TOGETHER','CHANGING CONDITIONS','STATED INTENT|COMPETITIVE EFFECT'),
 ('Here is','title','HEAR THE EXPLANATION','TRICK2G  →  ORIGINAL AUDIO','green')],
'A5':[
 ('Now look','title','THE MISSING DETAIL','WHO WAS THE FRIEND?','green'),
 ('Reporting identifies','title','ALICOPTER','THE FRIEND IDENTIFIED IN REPORTING','green'),
 ('already a','compare','CHALLENGER','GOLD IN FLEX','PLAYER’S SKILL|QUEUE PLACEMENT'),
 ('That supports','title','NOT A BEGINNER','WHY TRICK2G DISPUTED THE FRAMING','green'),
 ('It does not','title','NOT THE WHOLE TEST','ACCOUNT SWITCHING STILL MATTERS','red'),
 ('A player’s','compare','PLAYER SKILL','ACCOUNT RANK','RELATED|NOT IDENTICAL')],
'B1':[
 ('Riot’s Drew','title','DREW LEVIN','RIOT / LEAGUE OF LEGENDS LEADERSHIP','green'),
 ('using alternate','flow','THE INITIAL REPLY','LEVIN’S INTERPRETATION','HIGH-RANK PLAYERS|ALTS|GOLD → EMERALD'),
 ('was basically','quote','“basically the\ndefinition of boosting”','DREW LEVIN / RESPONSE TO TRICK2G','EXCERPT • AS QUOTED BY SPORTSKEEDA'),
 ('That was','title','AN INTERPRETATION','NOT THE COMPLETE MATCH EVIDENCE','red'),
 ('The dispute','title','WHAT WAS\nBEING PUNISHED?','THE CORE QUESTION','green')],
'B2':[
 ('Then came','title','THE APOLOGY','18 SEPTEMBER 2026','green'),
 ('Levin called','quote','“off the cuff\nand incurious”','DREW LEVIN / ON HIS EARLIER REPLY','EXCERPT • AS QUOTED BY SPORTSKEEDA'),
 ('He said','flow','DIRECT CONTACT','RIOT SAID IT WAS SPEAKING WITH THE GROUP','RIOT|STREAMERS|CLARITY'),
 ('and admitted','quote','“not something we’ve\nbeen clear enough on”','DREW LEVIN / PLAYING WITH FRIENDS','EXCERPT • AS QUOTED BY SPORTSKEEDA'),
 ('But he also','title','THE STANCE REMAINS','SMURFING + BOOSTING','red'),
 ('An apology','compare','APOLOGY','BAN REVERSAL','CONFIRMED STATEMENT|NOT ESTABLISHED HERE'),
 ('The reporting','title','OUTCOME NOT ESTABLISHED','NO CONFIRMED REVERSAL IN REVIEWED REPORTING','green')],
'A6':[
 ('So the payoff','title','NOT THAT SIMPLE','NO “FRIENDSHIP IS ILLEGAL” CONCLUSION','green'),
 ('It is that','flow','THE REAL BOUNDARY','THREE QUESTIONS, NOT ONE','WHO YOU QUEUE WITH|WHICH ACCOUNT|WHICH RULE'),
 ('which account','flow','WHICH ACCOUNT?','FRIENDSHIP ALONE DOES NOT SETTLE IT','PLAYER|ACCOUNT|RANK'),
 ('Trainwrecks asked','hero','THE QUESTION\nREMAINS','TRAINWRECKS / ARCHIVE PORTRAIT','train'),
 ('Riot promised','title','CLEARER GUIDANCE','PROMISED BY RIOT','green'),
 ('Whether that','title','STILL AN OPEN DISPUTE','REPORTING REVIEWED / 20 SEPTEMBER 2026','green'),
 ('Subscribe','title','FOLLOW THE EVIDENCE.','SUBSCRIBE FOR THE NEXT VERIFIED UPDATE','green')]
}
SOURCES={'A1':'[1,2] Sportskeeda + NDTV • 19 Sep | portrait: archive / Sportskeeda', 'A2':'[1] Sportskeeda • 18–19 Sep | [4] @TrainUpdates / X', 'A3':'[2] NDTV • 19 Sep | [6] Riot Games / X • 17 Sep', 'A4':'[1,2] Sportskeeda + NDTV | [5] @Trick2g / X', 'A5':'[1,3] Sportskeeda + NERFPLZ • 18–19 Sep', 'B1':'[1] Sportskeeda • 19 Sep | [7] Drew Levin / X', 'B2':'[1,2] Sportskeeda + NDTV • 19 Sep | [8] Drew Levin / X', 'A6':'[1,2] Sportskeeda + NDTV • latest reviewed reporting: 19 Sep'}
CH={'A1':'01 / The hook','A2':'02 / The streamer','A3':'03 / The crackdown','A4':'04 / The turning point','A5':'05 / The missing detail','B1':'06 / The escalation','B2':'07 / The consequences','A6':'08 / The open question'}
def render(id,layout,title,sub,arg):
 im=base(CH.get(id,'ORIGINAL AUDIO'),SOURCES.get(id,'Original source clip • links in README'))
 d=ImageDraw.Draw(im)
 if layout=='hero':
  circle(im,SRC/f'{arg}_portrait.jpg',(820,133,1195,508))
  txt(im,(64,126),'THE STREAMER’S SIDE',18,GREEN)
  lines(im,(62,205),title,67,width=730,step=82)
  lines(im,(65,449),sub,19,MUTED,width=720)
 elif layout=='duo':
  circle(im,SRC/'train_portrait.jpg',(155,122,475,442));circle(im,SRC/'trick_portrait.jpg',(805,122,1125,442),RED)
  txt(im,(589,237),'×',72,MUTED)
  txt(im,(227,452),'TRAINWRECKS',22);txt(im,(905,452),'TRICK2G',22)
  txt(im,(393,518),sub,20,GREEN)
 elif layout=='number':
  txt(im,(68,125),'THE SCALE OF ENFORCEMENT',20,GREEN)
  txt(im,(58,183),title,170,WHITE)
  txt(im,(71,404),sub,35,GREEN)
  txt(im,(73,482),arg,22,MUTED)
 elif layout=='quote':
  d.rounded_rectangle((67,123,1210,533),radius=14,fill='#111a1e',outline='#334940',width=2)
  d.rectangle((67,143,75,507),fill=GREEN)
  txt(im,(106,150),arg,16,GREEN)
  lines(im,(105,214),title,49,width=1050,step=65)
  txt(im,(108,477),sub,21,MUTED)
 elif layout=='compare':
  d.rounded_rectangle((65,140,615,525),radius=14,fill='#142117',outline='#3c6041',width=2)
  d.rounded_rectangle((660,140,1210,525),radius=14,fill='#25191d',outline='#684149',width=2)
  left,right=arg.split('|');txt(im,(91,180),left,19,GREEN);txt(im,(686,180),right,19,RED)
  lines(im,(90,281),title,49,width=500,step=64)
  lines(im,(685,281),sub,49,width=500,step=64)
  txt(im,(620,438),'≠',34,MUTED)
 elif layout=='flow':
  lines(im,(65,137),title,54,width=1160)
  txt(im,(68,219),sub,23,MUTED)
  for i,label in enumerate(arg.split('|')):
   x=66+i*399
   d.rounded_rectangle((x,328,x+350,471),radius=12,fill='#13211a',outline='#45633a',width=2)
   txt(im,(x+18,345),'0'+str(i+1),17,GREEN)
   lines(im,(x+18,384),label,25,width=322,step=31)
   if i<2:txt(im,(x+357,376),'→',30,GREEN)
 elif layout=='photo':
  txt(im,(65,115),title,36)
  photo(im,SRC/arg,(240,172,1040,541));txt(im,(65,547),sub,15,MUTED)
 elif layout=='notice':
  photo(im,SRC/'notice.jpg',(300,110,980,543))
 else:
  color=RED if arg=='red' else GREEN
  txt(im,(67,143),'KICK DRAMA / LEAGUE OF LEGENDS',18,color)
  maxsize=84 if max(len(l) for l in title.split('\n'))<22 else 64
  lines(im,(62,229),title,maxsize,width=1160,step=int(maxsize*1.15))
  lines(im,(68,484),sub,25,MUTED,width=1125)
 return im

def norm(s):return re.sub('[^a-z0-9]','',s.lower())
def cue_time(seg,cue):
 words=seg['words'];n=[norm(w['word']) for w in words];q=[norm(w) for w in cue.split()]
 for i in range(len(n)-len(q)+1):
  if n[i:i+len(q)]==q:return words[i]['start']
 raise ValueError((seg['id'],cue))

def main():
 T=json.loads((ROOT/'timings.json').read_text());shots=[]
 for seg in T['segments']:
  id=seg['id']
  if seg['kind']=='narration':
   defs=D[id]
   starts=[0]+[cue_time(seg,c[0]) for c in defs[1:]]
   # Enforce 2–6 second beats with additional closeups/reframes where needed.
   for j,((cue,layout,title,sub,arg),start) in enumerate(zip(defs,starts)):
    end=starts[j+1] if j+1<len(starts) else seg['dur']
    image=render(id,layout,title,sub,arg);name=f'{id}_{j:02d}.jpg';image.save(GFX/name,quality=94)
    if end-start<.4:continue
    parts=max(1,math.ceil((end-start)/6))
    for k in range(parts):
     a=round((seg['start']+start+(end-start)*k/parts)*30)/30;b=round((seg['start']+start+(end-start)*(k+1)/parts)*30)/30
     shots.append({'id':f'{id}_{j:02d}_{k}','kind':'still','image':name,'start':a,'dur':b-a,'variant':k,'chapter':id})
  elif seg['kind']=='clip':
   frame=base('SOURCE CLIP / ORIGINAL AUDIO',seg['source']);txt(frame,(56,100),seg['speaker'],24,GREEN)
   txt(frame,(890,103),'ORIGINAL AUDIO',18,RED)
   frame.save(GFX/f'{id}_frame.jpg',quality=95)
   # True source footage continues through motivated punch-ins; no voiceover overlap.
   n=math.ceil(seg['dur']/5.5)
   for j in range(n):
    a=round((seg['start']+seg['dur']*j/n)*30)/30;b=round((seg['start']+seg['dur']*(j+1)/n)*30)/30
    shots.append({'id':f'{id}_{j}','kind':'clip','file':seg['file'],'image':f'{id}_frame.jpg','cut':seg['cut']+(a-seg['start']),'start':a,'dur':b-a,'variant':j%2,'chapter':id})
  else:
   im=render('A6','title','FOLLOW THE EVIDENCE.','SOURCES + TRANSCRIPT INCLUDED / 20 SEP 2026','green');im.save(GFX/'end.jpg',quality=94)
   shots.append({'id':'END','kind':'still','image':'end.jpg','start':seg['start'],'dur':seg['dur'],'variant':0,'chapter':'END'})
 (ROOT/'shots.json').write_text(json.dumps(shots,indent=2));print(len(shots),'shots')
 # Thumbnail: no fabricated expressions, no fake platform ban.
 im=ImageOps.fit(Image.open(SRC/'bg_ai.png').convert('RGB'),(1280,720))
 circle(im,SRC/'train_portrait.jpg',(790,96,1235,541));circle(im,SRC/'trick_portrait.jpg',(998,446,1244,692),RED)
 txt(im,(62,63),'KICK’S RANK DISPUTE',29,GREEN)
 lines(im,(53,181),'BANNED FOR\nFRIENDS?',93,WHITE,width=755,step=110)
 ImageDraw.Draw(im).rounded_rectangle((60,476,728,553),radius=8,fill=RED)
 txt(im,(84,492),'THE LEAGUE OF LEGENDS BANS',27,'#080c10')
 txt(im,(64,620),'TRAINWRECKS × TRICK2G',26,MUTED)
 im.save(ROOT/'thumbnail.jpg',quality=95)
if __name__=='__main__':main()

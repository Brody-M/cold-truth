"""Draft captions and exact-audio review player. No approval or video render."""
from pathlib import Path
from datetime import datetime, timezone
import hashlib
import html
import json
import os
from PIL import ImageFont

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
CASE = HERE.parent
AUDIO = CASE / 'Audio/full_repair_05'
VIS = CASE / 'Visuals/Longform/revision_05'
TIMING = AUDIO / 'remapped_word_timing_draft.json'
FONT = ImageFont.truetype('C:/Windows/Fonts/segoeui.ttf', 44)
MAX_WIDTH = 1560

def describe(p):
    return {'path':p.relative_to(ROOT).as_posix(),'bytes':p.stat().st_size,
            'sha256':hashlib.sha256(p.read_bytes()).hexdigest()}

def relative(p):
    return os.path.relpath(p, HERE).replace('\\','/')

def balance(text):
    words = text.split()
    if len(text) <= 48 and FONT.getlength(text) <= MAX_WIDTH:
        return text
    options = []
    for i in range(1,len(words)):
        left,right=' '.join(words[:i]),' '.join(words[i:])
        widths=FONT.getlength(left),FONT.getlength(right)
        if max(widths)<=MAX_WIDTH:
            penalty=abs(widths[0]-widths[1])
            if words[i-1].endswith((',',':',';')):
                penalty-=70
            if len(words[i:])<=2 or len(words[:i])<=2:
                penalty+=140
            if words[i-1].lower().strip(',.;:') in {'the','a','an','and','but','or','of','to','for'}:
                penalty+=90
            options.append((penalty,left+'\n'+right))
    assert options, 'Cannot fit two lines: '+text
    return min(options,key=lambda x:x[0])[1]

def move_trailing_connectors(groups, words):
    moved=0
    weak={'the','a','an','but','and','or','to','of','for','with','from','in','by','as','at'}
    for a,b in zip(groups,groups[1:]):
        while a['word_end_exclusive']-a['word_start']>4:
            last=a['word_end_exclusive']-1
            if words[last]['word'].lower() not in weak:break
            if words[last-1]['end']-a['start']<.85:break
            text=' '.join(w['word'] for w in words[last:b['word_end_exclusive']])
            if b['end']-words[last]['start']>5.5 or len(text)>92:break
            balance(text)
            a['word_end_exclusive']=last;a['end']=words[last-1]['end']
            a['text']=' '.join(w['word'] for w in words[a['word_start']:last])
            b['word_start']=last;b['start']=words[last]['start'];b['text']=text;moved+=1
    return moved

def srt_time(t):
    ms=round(t*1000);h,ms=divmod(ms,3600000);m,ms=divmod(ms,60000);s,ms=divmod(ms,1000)
    return f'{h:02}:{m:02}:{s:02},{ms:03}'

def ass_time(t):
    cs=round(t*100);h,cs=divmod(cs,360000);m,cs=divmod(cs,6000);s,cs=divmod(cs,100)
    return f'{h}:{m:02}:{s:02}.{cs:02}'

if __name__=='__main__':
    outputs=[VIS/'captions_paced_draft.json',VIS/'captions_paced_draft.srt',VIS/'captions_paced_draft.ass',HERE/'Audio_Candidate_05_Review.html',HERE/'candidate_review_05_preparation.json']
    assert all(not p.exists() for p in outputs), 'Refusing to overwrite prepared review'
    timing=json.loads(TIMING.read_text(encoding='utf-8'))
    approved=(HERE/'Narration_Text.txt').read_text(encoding='utf-8')
    words=timing['word_segments']
    assert [w['word'] for w in words]==approved.split()
    assert timing['assembly_allowed'] is False
    old=json.loads((HERE/'alignment.json').read_text(encoding='utf-8'))['segments']
    cursor=0;groups=[]
    for segment in old:
        tokens=segment['text'].split();end=cursor+len(tokens)
        assert [w['word'] for w in words[cursor:end]]==tokens
        groups.append({'word_start':cursor,'word_end_exclusive':end,
                       'start':words[cursor]['start'],'end':words[end-1]['end'],
                       'text':' '.join(tokens)})
        cursor=end
    assert cursor==len(words)==1267
    # Merge short orphan cues only when the actual new time span and line widths fit.
    i=0;merges=0
    while i<len(groups):
        g=groups[i]
        if g['end']-g['start']<.85 or g['word_end_exclusive']-g['word_start']<=2:
            choices=([i-1] if i else [])+([i+1] if i+1<len(groups) else [])
            merged=False
            for j in choices:
                lo,hi=sorted((i,j));a,b=groups[lo],groups[hi]
                text=a['text']+' '+b['text']
                if b['end']-a['start']<=5.5 and len(text)<=92:
                    balance(text)
                    groups[lo:hi+1]=[{'word_start':a['word_start'],'word_end_exclusive':b['word_end_exclusive'],
                                    'start':a['start'],'end':b['end'],'text':text}]
                    i=max(0,lo-1);merges+=1;merged=True;break
            if merged:continue
        i+=1
    trailing_moves=move_trailing_connectors(groups,words)
    for g in groups:
        g['text']=balance(g['text'])
        assert len(g['text'].splitlines())<=2
        assert max(FONT.getlength(line) for line in g['text'].splitlines())<=MAX_WIDTH
        assert 0<g['end']-g['start']<=5.5+1e-9
    assert ' '.join(g['text'].replace('\n',' ') for g in groups).split()==approved.split()
    assert all(a['end']<=b['start'] for a,b in zip(groups,groups[1:]))
    captions={'schema_version':'cold_truth.paced_caption_draft.v1','created_at_utc':datetime.now(timezone.utc).isoformat(),
              'status':'DRAFT_REQUIRES_EXACT_AUDIO_AND_TIMING_REVIEW','audio':timing['audio'],
              'word_timing_draft':describe(TIMING),'approved_text':describe(HERE/'Narration_Text.txt'),
              'source_caption_groups':describe(HERE/'alignment.json'),'maximum_lines':2,
              'font':'Segoe UI44px','maximum_measured_line_width_px':MAX_WIDTH,'short_orphan_groups_merged':merges,
              'old_group_count':len(old),'new_group_count':len(groups),'spoken_words':1267,
              'trailing_connector_words_moved_to_next_cue':trailing_moves,
              'human_audio_approved':False,'human_timing_approved':False,'assembly_allowed':False,
              'actual_burned_caption_layout_reviewed':False,'segments':groups}
    outputs[0].write_text(json.dumps(captions,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
    outputs[1].write_text('\n\n'.join(f'{n}\n{srt_time(g["start"])} --> {srt_time(g["end"])}\n{g["text"]}' for n,g in enumerate(groups,1))+'\n',encoding='utf-8')
    header='''[Script Info]
ScriptType: v4.00+
PlayResX: 1920
PlayResY: 1080
WrapStyle: 2

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Default,Segoe UI,44,&H00FFFFFF,&H00FFFFFF,&H00000000,&H60000000,0,0,0,0,100,100,0,0,1,2.5,1,2,100,100,110,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
'''
    events=[]
    for g in groups:
        text=g['text'].replace('\n',r'\N')
        assert '{' not in text and '}' not in text and '\\' not in text.replace(r'\N','')
        events.append(f'Dialogue: 0,{ass_time(g["start"])},{ass_time(g["end"])},Default,,0,0,0,,{text}')
    outputs[2].write_text(header+'\n'.join(events)+'\n',encoding='utf-8')
    receipt=json.loads((AUDIO/'full_repair_05_receipt.json').read_text(encoding='utf-8'))
    examples=''.join('<section class="pair"><h3>'+html.escape(x['label'].title())+' · paragraph '+str(x['paragraph_id'])+'</h3><label>Before, original pacing<audio controls preload="none" src="'+html.escape(relative(Path(x['before']['path'])),quote=True)+'"></audio></label><label>Proposed pacing<audio controls preload="none" src="'+html.escape(relative(Path(x['after']['path'])),quote=True)+'"></audio></label><p>'+html.escape(x['complete_approved_paragraph_text'])+'</p></section>' for x in receipt['actual_paragraph_comparisons'])
    paragraphs=''.join('<section class="paragraph"><h3><button type="button" onclick="seek('+str(p['start'])+')">'+str(p['paragraph_id'])+' · '+str(int(p['start']//60))+':'+str(int(p['start']%60)).zfill(2)+'</button></h3><p>'+''.join('<button class="word '+('flag' if w['score']<.6 else '')+'" id="w'+str(w['original_word_index'])+'" data-t="'+str(w['start'])+'">'+html.escape(w['word'])+'</button> ' for w in words[p['word_start_index']:p['word_end_index_exclusive']])+'</p></section>' for p in timing['paragraphs'])
    player_data=json.dumps({'words':words,'captions':groups},ensure_ascii=False).replace('<',r'\u003c')
    page='''<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Amy · audio candidate05</title><style>
    :root{color-scheme:dark}body{margin:0;background:#10151a;color:#eee8df;font:17px/1.6 "Segoe UI",sans-serif}main{max-width:1050px;margin:auto;padding:30px 24px}h1{font-size:32px;line-height:1.2}h2{margin-top:36px}.status{background:#332a1e;border-left:4px solid #d4a65b;padding:15px}.player{position:sticky;top:0;background:#182129f2;padding:14px;z-index:2;border-bottom:1px solid #53606b}audio{display:block;width:100%;margin:8px 0}.caption{min-height:66px;text-align:center;white-space:pre-line;font-size:22px}.pair{border-top:1px solid #39444e;padding-top:12px}.pair label{display:inline-block;width:48%;vertical-align:top}.pair p{font-size:15px;color:#b9c3cb}button{cursor:pointer;background:#25323d;color:inherit;border:0;border-radius:4px;padding:4px 7px;font:inherit}.word{background:transparent;padding:1px 3px;line-height:1.75}.flag{border-bottom:2px dotted #e1b464}.active{background:#3f6069}.paragraph{border-bottom:1px solid #2c3740}a{color:#a7c9d1}@media(max-width:650px){.pair label{display:block;width:100%}.player{position:relative}}</style><main><h1>Amy · full audio candidate05</h1><p class="status"><strong>Listening and timing review pending.</strong> This is an existing take with targeted onset repair and104 quiet-gap edits. No new speech generation. Every approved spoken word is retained. This page cannot approve or publish media.</p><p>Full candidate:9:08.59. Compare complete paragraphs below, then play the whole track for pronunciation, comfortable level, natural joins and story flow. Click a word to check synchronization; amber underlines indicate lower-confidence original alignment.</p><div class="player"><strong>Exact paced WAV · 44.1kHz mono</strong><audio id="full" controls preload="metadata" src="AUDIO_SOURCE"></audio><div id="caption" class="caption"></div><small id="position">0:00</small></div><p><a href="ORIGINAL_SOURCE">Original-timing repaired MP3 ·9:30.56</a> · <a href="PACED_SOURCE">Paced MP3 ·9:08.59</a></p><h2>Complete-paragraph comparisons</h2>EXAMPLES<h2>Word timing · draft</h2>PARAGRAPHS<script>
    const data=PLAYER_DATA;const audio=document.getElementById('full');let active=-1;let frame;
    function seek(t){audio.currentTime=t;audio.play().catch(()=>{});update()}
    document.querySelectorAll('.word').forEach(b=>b.addEventListener('click',()=>seek(Number(b.dataset.t))));
    function find(list,t){let lo=0,hi=list.length-1,result=-1;while(lo<=hi){const mid=(lo+hi)>>1;if(list[mid].start<=t){result=mid;lo=mid+1}else hi=mid-1}return result>=0&&t<=list[result].end?result:-1}
    function update(){cancelAnimationFrame(frame);const t=audio.currentTime;const i=find(data.words,t);if(active!==i){if(active>=0)document.getElementById('w'+active).classList.remove('active');if(i>=0)document.getElementById('w'+i).classList.add('active');active=i}const c=find(data.captions,t);document.getElementById('caption').textContent=c>=0?data.captions[c].text:'';document.getElementById('position').textContent=Math.floor(t/60)+':'+String(Math.floor(t%60)).padStart(2,'0');if(!audio.paused)frame=requestAnimationFrame(update)}
    audio.addEventListener('play',()=>{cancelAnimationFrame(frame);update()});audio.addEventListener('pause',()=>{cancelAnimationFrame(frame);update()});audio.addEventListener('seeked',update);
    </script></main></html>'''
    page=page.replace('AUDIO_SOURCE',html.escape(relative(AUDIO/'Amy_Mihaljevic_Mia_full_repair_05_pacing_candidate.wav'),quote=True)).replace('ORIGINAL_SOURCE',html.escape(relative(AUDIO/'Amy_Mihaljevic_Mia_full_repair_05_original_timing.mp3'),quote=True)).replace('PACED_SOURCE',html.escape(relative(AUDIO/'Amy_Mihaljevic_Mia_full_repair_05_pacing_candidate.mp3'),quote=True)).replace('EXAMPLES',examples).replace('PARAGRAPHS',paragraphs).replace('PLAYER_DATA',player_data)
    outputs[3].write_text(page,encoding='utf-8')
    result={'schema_version':'cold_truth.audio_review_preparation.v1','recorded_at_utc':datetime.now(timezone.utc).isoformat(),'processor':describe(Path(__file__)),'inputs':[describe(TIMING),describe(HERE/'Narration_Text.txt'),describe(HERE/'alignment.json')],'caption_groups_before':len(old),'caption_groups_after':len(groups),'short_orphan_groups_merged':merges,'three_line_cues':0,'maximum_segment_seconds':max(g['end']-g['start'] for g in groups),'exact1267_word_sequence':True,'all_times_monotonic':True,'player_word_buttons':page.count('class="word '),'external_requests':False,'actual_browser_playback_tested':False,'human_audio_approved':False,'human_timing_approved':False,'assembly_allowed':False,'outputs':[describe(p) for p in outputs[:-1]]}
    outputs[-1].write_text(json.dumps(result,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
    print(json.dumps({k:result[k] for k in ['caption_groups_before','caption_groups_after','short_orphan_groups_merged','three_line_cues','maximum_segment_seconds','player_word_buttons']},indent=2))

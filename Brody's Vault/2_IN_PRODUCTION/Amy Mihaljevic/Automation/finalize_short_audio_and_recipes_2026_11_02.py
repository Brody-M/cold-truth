"""Bind real playback decisions and prepare three existing-scope Orbital cuts."""
from pathlib import Path
from datetime import datetime,timezone
import json,sys,re,math,shutil
from PIL import ImageFont

A=Path(__file__).resolve().parent; C=A.parent; ROOT=A.parents[3]
sys.path.insert(0,str(ROOT))
from automation import pilot_evidence as pe
def read(p): return json.loads(p.read_text(encoding='utf-8'))
def desc(p): return pe.describe(ROOT,p.relative_to(ROOT).as_posix())
def write(p,d):
    if p.exists():
        assert read(p)==d, f'Changed preparation artifact: {p}'
        return
    p.write_text(json.dumps(d,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
def stamp(seconds):
    centiseconds=round(seconds*100); minutes,cs=divmod(centiseconds,6000); hours,minute=divmod(minutes,60)
    return f'{hours}:{minute:02}:{cs//100:02}.{cs%100:02}'
def wrap(text,font,width,maxlines):
    lines=[]; line=[]
    for token in text.split():
        candidate=' '.join(line+[token])
        if line and font.getlength(candidate)>width: lines.append(' '.join(line)); line=[token]
        else: line.append(token)
    if line: lines.append(' '.join(line))
    if len(lines)>maxlines or any(font.getlength(line)>width for line in lines): return None
    return '\n'.join(lines)
def captions(words,font):
    groups=[]; current=[]
    for word in words:
        proposed=current+[word]
        if current and (word['end']-current[0]['start']>4.8 or wrap(' '.join(w['word'] for w in proposed),font,760,2) is None):
            groups.append(current); current=[]
        current.append(word)
        if word['word'].endswith(('.', '?','!',';')) and len(current)>=3:
            groups.append(current); current=[]
    if current: groups.append(current)
    result=[dict(start=g[0]['start'],end=g[-1]['end'],text=wrap(' '.join(w['word'] for w in g),font,760,2)) for g in groups]
    assert all(s['text'] and s['end']-s['start']<=6 for s in result)
    return result
def ass_text(text): return text.replace('\\','\\\\').replace('{',r'\{').replace('}',r'\}').replace('\n',r'\N')
def cue_tokens(text):
    # Cue headings use the base name; narration may use the same name possessively.
    return [w[:-2] if w.endswith(("'s",'’s')) else w for w in pe.words(text)]

def main():
    pending=read(A/'pending_review02_playback_2026_11_02.json')
    for key in ('video','approved_audio','review_note','player','render_receipt','export_audit'): pe.bound(ROOT,pending[key])
    packet=read(A/'shorts_audio_review_packet_01.json')
    for entry in packet['entries']:
        for key in ('audio','preview','script','phase_2_scope','timing_draft'): pe.bound(ROOT,entry[key])
    pe.bound(ROOT,packet['review_player'])
    approval=dict(schema_version='cold_truth.video_and_short_audio_review_decisions.v1',recorded_at_utc=datetime.now(timezone.utc).isoformat(),human_approved=True,approved_by='Brody',approved_on='2026-11-02',user_quote='Watched fully; approve this video',scope='Full exact9:08.63 corrective cut02: visuals, actual crop/motion, captions, pacing, audio, synchronization and ending. Not publishing or another long-form render.',question_item_id='["request_user_input_async","call_691024e1ffa74797aaac42488502bda0",0]',video=pending['video'],video_review_request=desc(A/'pending_review02_playback_2026_11_02.json'),short_audio_timing=dict(human_approved=True,approved_by='Brody',approved_on='2026-11-02',user_quote='Listened and checked; approve all three',scope='All three exact existing processed Short WAVs: full pronunciation, completeness, volume and synchronization against matching word-timing drafts.',question_item_id='["request_user_input_async","call_691024e1ffa74797aaac42488502bda0",1]',full_listen_passed=True,packet=desc(A/'shorts_audio_review_packet_01.json')),new_provider_calls=0,publishing_authorized=False)
    receipt=A/'approvals/review02_and_short_audio_approved_2026_11_02.json'
    if receipt.exists():
        existing=read(receipt)
        assert existing['video']==approval['video'] and existing['video_review_request']==approval['video_review_request']
        assert existing['user_quote']==approval['user_quote'] and existing['short_audio_timing']==approval['short_audio_timing']
        approval=existing
    else: write(receipt,approval)
    proposal=read(A/'next_production_scope_2026_10_21.json')
    authority=read(A/'approvals/phase_2_review_production_2026_10_21.json'); pe.decision(authority); pe.bound(ROOT,authority['proposal'])
    assert proposal['limits']['maximum_review_renders_per_video']==2 and proposal['limits']['maximum_new_output_bytes']==5*1024**3
    registry=read(A/'asset_registry.json'); isolated=pe.assets(ROOT,desc(A/'asset_registry.json')['path'])
    orbital=registry['shorts'][0]; assert orbital['asset_class']=='orbital_gameplay'
    font=ImageFont.truetype('C:/Windows/Fonts/segoeuib.ttf',54)
    overlay_font=ImageFont.truetype('C:/Windows/Fonts/segoeuib.ttf',44)
    output=[]
    for entry,branch in zip(packet['entries'],proposal['shorts_branches']):
        folder=(ROOT/entry['script']['path']).parent; ba=folder/'Automation'
        request=read(ba/'audio_preflight_request.json')
        if (ba/'review_video_recipe_01.json').exists():
            previous=read(ba/'review_video_recipe_01.json')
            for key in ('script','audio','alignment','preflight','subtitles','actual_audio_timing_approval'): pe.bound(ROOT,previous[key])
            pe.alignment(ROOT,desc(ba/'alignment.json')['path'],pe.audio_preflight(ROOT,desc(ba/'audio_preflight_request.json')['path']))
            output.append(desc(ba/'review_video_recipe_01.json')); continue
        archived=ba/'archive/before_actual_audio_approval_2026_11_02'
        if not archived.exists():
            archived.mkdir(parents=True)
            shutil.copy2(ba/'audio_preflight_request.json',archived/'audio_preflight_request.json')
        decision=dict(approval['short_audio_timing']); decision['decision_receipt']=desc(receipt)
        qa=read(ba/'audio_qa_01.json'); qa.update(decision); qa.update(assembly_allowed=True,issues=[],status='FULL_AUDIO_AND_TIMING_APPROVED')
        qap=ba/'audio_qa_approved_2026_11_02.json'; write(qap,qa)
        request['audio_qa']=desc(qap)
        (ba/'audio_preflight_request.json').write_text(json.dumps(request,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
        preflight=pe.audio_preflight(ROOT,desc(ba/'audio_preflight_request.json')['path']); assert preflight['assembly_allowed'] and 30<=preflight['narration_duration_seconds']<=60
        write(ba/'preflight.json',preflight)
        draft=read(ROOT/entry['timing_draft']['path']); groups=captions(draft['word_segments'],font)
        alignment=dict(schema_version='cold_truth.reviewed_alignment.v1',case_id=entry['case_id'],target_format='shorts',audio=request['audio'],script=request['script'],narration_text=request['narration_text'],tool='Existing reviewed offline word timing; lossless caption grouping from unchanged words/times',recorded_at_utc=approval['recorded_at_utc'],reviewed_machine_draft=entry['timing_draft'],segments=groups,timing_review=decision,caption_style=dict(font='Segoe UI Bold54px',maximum_lines=2,maximum_line_width_px=760,position=[490,1160]))
        write(ba/'alignment.json',alignment); pe.alignment(ROOT,desc(ba/'alignment.json')['path'],preflight)
        subtitle=folder/'Audio'/f'Amy_Short_{entry["id"]:02}.srt'
        if subtitle.exists(): assert subtitle.read_text(encoding='utf-8')==pe.srt(alignment)
        else: subtitle.write_text(pe.srt(alignment),encoding='utf-8')
        text=(ROOT/entry['script']['path']).read_text(encoding='utf-8')
        cues=re.findall(r'^\|\s*(.*?)\s*\|\s*\[OVERLAY:\s*(.*?)\]\s*\|\s*$',text,re.M)
        assert len(cues)==(7 if entry['id']==3 else 6)
        flat=[]; owners=[]
        for i,w in enumerate(draft['word_segments']):
            tokens=cue_tokens(w['word']); flat.extend(tokens); owners.extend([i]*len(tokens))
        overlays=[]; cursor=0
        for cue,overlay in cues:
            wanted=cue_tokens(cue)
            found=next((i for i in range(cursor,len(flat)-len(wanted)+1) if flat[i:i+len(wanted)]==wanted),None)
            assert found is not None, f'Missing exact cue: {cue}'
            cursor=found+len(wanted); start=draft['word_segments'][owners[found]]['start']
            wrapped=wrap(overlay,overlay_font,760,3); assert wrapped is not None,overlay
            overlays.append(dict(cue=cue,text=wrapped,start=start))
        duration=preflight['narration_duration_seconds']
        for i,o in enumerate(overlays):
            o['end']=min(duration,o['start']+7,overlays[i+1]['start'] if i+1<len(overlays) else duration)
            assert o['end']>o['start'] and o['end']-o['start']>=1.0
        visual=folder/'Visuals'; visual.mkdir(exist_ok=True)
        ass=visual/'review_01.ass'; assert not ass.exists()
        header='''[Script Info]
ScriptType: v4.00+
PlayResX: 1080
PlayResY: 1920
WrapStyle: 2
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Caption,Segoe UI,54,&H00FFFFFF,&H00FFFFFF,&H00000000,&H70000000,-1,0,0,0,100,100,0,0,1,3,1,5,100,220,0,1
Style: Fact,Segoe UI,44,&H00FFFFFF,&H00FFFFFF,&H00000000,&H60000000,-1,0,0,0,100,100,0,0,3,14,0,8,100,220,250,1
Style: Credit,Segoe UI,24,&H00FFFFFF,&H00FFFFFF,&H00000000,&H70000000,0,0,0,0,100,100,0,0,1,2,0,2,100,220,340,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
'''
        events=[]
        for s in groups: events.append(f"Dialogue: 1,{stamp(s['start'])},{stamp(s['end'])},Caption,,0,0,0,,{{\\pos(490,1160)}}{ass_text(s['text'])}")
        for o in overlays: events.append(f"Dialogue: 2,{stamp(o['start'])},{stamp(o['end'])},Fact,,0,0,0,,{ass_text(o['text'])}")
        events.append(f"Dialogue: 0,{stamp(0)},{stamp(duration)},Credit,,0,0,0,,Gameplay footage by Orbital -\\NNo Copyright Gameplay")
        ass.write_text(header+'\n'.join(events)+'\n',encoding='utf-8')
        assert branch['review_outputs'][0] in read(ROOT/entry['phase_2_scope']['path'])['output_paths']
        recipe=dict(schema_version='cold_truth.short_review_recipe.v1',case_id=entry['case_id'],id=entry['id'],target_format='shorts',created_at_utc=approval['recorded_at_utc'],authority=desc(A/'approvals/phase_2_review_production_2026_10_21.json'),branch_authority=entry['phase_2_scope'],actual_audio_timing_approval=desc(receipt),script=entry['script'],audio=entry['audio'],preflight=desc(ba/'preflight.json'),audio_request=desc(ba/'audio_preflight_request.json'),alignment=desc(ba/'alignment.json'),subtitles=desc(ass),srt=desc(subtitle),registry=desc(A/'asset_registry.json'),gameplay=orbital,source_in_seconds=branch['proposed_gameplay_start_seconds'],source_audio=False,source_speed=1,source_looping=False,source_crop=dict(width=810,height=1440,x=875,y=0),output_width=1080,output_height=1920,fps=30,frames=math.ceil(duration*30),audio_duration_seconds=duration,caption_count=len(groups),overlays=overlays,required_gameplay_credit='Gameplay footage by Orbital - No Copyright Gameplay',output_path=branch['review_outputs'][0],working_directory=(C/f'Exports/Shorts/work_short_{entry["id"]:02}_review_01').relative_to(ROOT).as_posix(),maximum_output_bytes=5*1024**3,new_provider_calls=0,publishing_authorized=False,render_ready=True)
        write(ba/'review_video_recipe_01.json',recipe); output.append(desc(ba/'review_video_recipe_01.json'))
        print(f"Short{entry['id']}: {duration:.6f}s, {len(groups)} captions, {len(overlays)} approved-script overlays, preflight/alignment pass",flush=True)
    write(A/'shorts_review_preparation_2026_11_02.json',dict(status='THREE_SHORT_REVIEW_RECIPES_READY',approval=desc(receipt),isolation=isolated,recipes=output,new_provider_calls=0,publishing=False))

if __name__=='__main__': main()

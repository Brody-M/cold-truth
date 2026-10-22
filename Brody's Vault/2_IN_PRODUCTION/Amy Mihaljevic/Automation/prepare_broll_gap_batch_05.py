"""Four actual coverage-gap candidates; reuses the existing bounded downloader."""
from pathlib import Path
from datetime import datetime, timezone
import importlib.util
import json
import hashlib
import subprocess
from PIL import Image, ImageDraw, ImageFont

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
CASE = HERE.parent
SELECTION = HERE / 'pexels_broll_revision_05_gap_selected.json'
RECEIPT = HERE / 'broll_revision_05_gap_downloads.json'
QC = CASE / 'Visuals/Longform/revision_05/qc_gap'
RESULT = HERE / 'broll_revision_05_gap_technical_qc.json'

def describe(p):
    return {'path':p.relative_to(ROOT).as_posix(),'bytes':p.stat().st_size,
            'sha256':hashlib.sha256(p.read_bytes()).hexdigest()}

if __name__ == '__main__':
    assert not RESULT.exists() and not RECEIPT.exists()
    selected = json.loads(SELECTION.read_text(encoding='utf-8'))['entries']
    addendum = json.loads((HERE/'no_cost_broll_gap_addendum_05.json').read_text(encoding='utf-8'))
    assert len(selected) == addendum['maximum_additional_candidates'] == 4
    first = json.loads((HERE/'broll_revision_05_downloads.json').read_text(encoding='utf-8'))
    assert first['downloaded_bytes'] + sum(e['selected_file']['size'] for e in selected) < addendum['combined_revision_stock_bytes_cap']
    old = HERE/'download_pexels_01.py'
    spec = importlib.util.spec_from_file_location('original_bounded_stock_download', old)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    module.SELECTION, module.RECEIPT, module.CAP = SELECTION, RECEIPT, addendum['combined_revision_stock_bytes_cap']
    module.main()
    QC.mkdir(parents=True,exist_ok=True)
    result = {'schema_version':'cold_truth.gap_stock_qc.v1','recorded_at_utc':datetime.now(timezone.utc).isoformat(),
              'processor':describe(Path(__file__)),'reused_downloader':describe(old),
              'selection':describe(SELECTION),'scope':describe(HERE/'no_cost_broll_gap_addendum_05.json'),
              'entries':[],'human_rights_approved':False,'assembly_allowed':False}
    sheet = Image.new('RGB',(1440,1320),'#121820')
    font = ImageFont.truetype('C:/Windows/Fonts/segoeui.ttf',22)
    for row,e in enumerate(selected):
        video = ROOT/e['output_path']
        probe = subprocess.run(['ffprobe','-v','error','-show_streams','-show_format','-of','json',str(video)],capture_output=True,check=True)
        d = json.loads(probe.stdout);s = next(s for s in d['streams'] if s['codec_type']=='video');duration=float(d['format']['duration'])
        decoded = subprocess.run(['ffmpeg','-v','error','-nostdin','-threads','2','-i',str(video),'-map','0:v:0','-an','-f','null','-'],capture_output=True,timeout=180)
        log=QC/f'{e["provider_id"]}_decode.log';log.write_bytes(decoded.stderr)
        assert decoded.returncode==0 and not decoded.stderr
        frames=[]
        for col,fraction in enumerate((.1,.5,.9)):
            p=QC/f'{e["provider_id"]}_{col+1}.jpg'
            cmd=['ffmpeg','-v','error','-nostdin','-n','-ss',str(duration*fraction),'-i',str(video),'-frames:v','1','-q:v','2',str(p)]
            subprocess.run(cmd,capture_output=True,check=True,timeout=60)
            im=Image.open(p).convert('RGB');im.thumbnail((480,270));sheet.paste(im,(col*480+(480-im.width)//2,row*330+(270-im.height)//2));frames.append({'at_seconds':duration*fraction,'frame':describe(p),'command':cmd})
        ImageDraw.Draw(sheet).text((10,row*330+275),f'{e["provider_id"]} | {duration:.2f}s | {s["width"]}x{s["height"]}',font=font,fill='white')
        result['entries'].append({'asset_id':e['asset_id'],'source_identity':e['source_identity'],'file':describe(video),'probe':d,'width':s['width'],'height':s['height'],'duration_seconds':duration,'full_decode_passed':True,'decode_log':describe(log),'sampled_frames':frames})
    p=QC/'contact_sheet.jpg';sheet.save(p,quality=92);result['contact_sheet']=describe(p)
    result['completed_at_utc']=datetime.now(timezone.utc).isoformat();RESULT.write_text(json.dumps(result,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')

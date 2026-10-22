"""Bounded free-stock replacement candidates requested after video01 feedback."""
from pathlib import Path
from datetime import datetime, timezone
from urllib.parse import urlparse
import hashlib
import json
import urllib.request

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
CASE = HERE.parent
SELECTION = HERE / 'pexels_broll_revision_05_selected.json'
SCOPE = HERE / 'no_cost_continuation_scope_2026_10_21.json'
RECEIPT = HERE / 'broll_revision_05_downloads.json'
DEST = CASE / 'Visuals/Longform/revision_05/assets'
CAP = 750 * 1024**2
FILE_CAP = 60 * 1024**2
CASE_CAP = 5 * 1024**3

def describe(path):
    return {'path': path.relative_to(ROOT).as_posix(), 'bytes': path.stat().st_size,
            'sha256': hashlib.sha256(path.read_bytes()).hexdigest()}

def save(data):
    RECEIPT.write_text(json.dumps(data, indent=2, ensure_ascii=False)+'\n', encoding='utf-8')

if __name__ == '__main__':
    assert not RECEIPT.exists(), 'Inspect existing receipt before any further acquisition'
    data = json.loads(SELECTION.read_text(encoding='utf-8'))
    scope = json.loads(SCOPE.read_text(encoding='utf-8'))
    entries = data['entries']
    assert 0 < len(entries) <= scope['limits']['new_free_stock_candidates'] == 12
    assert 0 < sum(e['selected_file']['size'] for e in entries) < CAP
    assert len({e['provider_id'] for e in entries}) == len(entries)
    DEST.mkdir(parents=True, exist_ok=True)
    receipt = {'schema_version': 'cold_truth.free_broll_revision_downloads.v1',
               'started_at_utc': datetime.now(timezone.utc).isoformat(),
               'selection': describe(SELECTION), 'scope': describe(SCOPE),
               'processor': describe(Path(__file__)), 'status': 'STARTED',
               'automatic_retry': False, 'maximum_new_bytes': CAP,
               'paid_spending': 0, 'provider_credit_calls': 0, 'entries': []}
    save(receipt)
    total = 0
    case_before = sum(p.stat().st_size for p in CASE.rglob('*') if p.is_file())
    for entry in entries:
        variant = entry['selected_file']
        url = variant['link']
        assert urlparse(url).scheme == 'https' and urlparse(url).hostname == 'videos.pexels.com'
        assert variant['width'] >= 1920 and variant['height'] >= 1080
        assert 0 < variant['size'] <= FILE_CAP
        dest = (ROOT / entry['output_path']).resolve()
        assert dest.is_relative_to(DEST.resolve()) and not dest.exists()
        event = {'asset_id': entry['asset_id'], 'source_identity': entry['source_identity'],
                 'url': url, 'output_path': entry['output_path'],
                 'requested_at_utc': datetime.now(timezone.utc).isoformat(),
                 'api_reported_bytes': variant['size'], 'status': 'REQUESTED'}
        receipt['entries'].append(event)
        save(receipt)
        try:
            request = urllib.request.Request(url, headers={'User-Agent': 'ColdTruth-free-stock-revision/1.0'})
            with urllib.request.urlopen(request, timeout=45) as response:
                assert urlparse(response.url).scheme == 'https' and urlparse(response.url).hostname == 'videos.pexels.com'
                length = int(response.headers.get('Content-Length', '0'))
                assert 0 < length <= FILE_CAP and total+length <= CAP
                assert case_before+total+length < CASE_CAP
                event.update(cdn_bytes=length, api_cdn_size_difference=length-variant['size'])
                written = 0
                with dest.open('xb') as output:
                    while block := response.read(1024**2):
                        written += len(block)
                        assert written <= length and total+written <= CAP
                        output.write(block)
            assert written == length
            total += written
            event.update(status='DOWNLOADED_PENDING_CONTENT_AND_RIGHTS_REVIEW',
                         completed_at_utc=datetime.now(timezone.utc).isoformat(), output=describe(dest))
            save(receipt)
            print(json.dumps({'downloaded': entry['provider_id'], 'bytes': written}), flush=True)
        except Exception as error:
            event.update(status='FAILED_NO_RETRY', error_type=type(error).__name__, error=str(error))
            receipt['status'] = 'STOPPED_RECONCILIATION_REQUIRED'
            if dest.exists():
                event['partial_file'] = describe(dest)
            save(receipt)
            raise
    receipt.update(status='DOWNLOADED_TECHNICAL_CONTENT_RIGHTS_REVIEW_PENDING',
                   completed_at_utc=datetime.now(timezone.utc).isoformat(), downloaded_bytes=total,
                   human_rights_approved=False, assembly_allowed=False, video_rendered=False)
    save(receipt)

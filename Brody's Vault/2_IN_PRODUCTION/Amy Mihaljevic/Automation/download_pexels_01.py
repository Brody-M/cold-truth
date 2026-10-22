"""Download only the selected, authorized Pexels variants. No retries or rendering."""
from pathlib import Path
from datetime import datetime, timezone
from urllib.parse import urlparse
import hashlib
import json
import sys
import urllib.request

ROOT = Path(__file__).resolve().parents[4]
HERE = Path(__file__).resolve().parent
SELECTION = HERE / 'pexels_selected_sources_2026_10_21.json'
RECEIPT = HERE / 'pexels_download_receipt_01.json'
CAP = 2 * 1024 ** 3

def describe(path):
    return {'path': path.relative_to(ROOT).as_posix(), 'bytes': path.stat().st_size,
            'sha256': hashlib.sha256(path.read_bytes()).hexdigest()}

def save(data):
    RECEIPT.write_text(json.dumps(data, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')

def main():
    resume = '--resume-after-header-review' in sys.argv
    assert not RECEIPT.exists() or resume, 'Review prior download receipt before another invocation'
    selected = json.loads(SELECTION.read_text(encoding='utf-8'))
    assert 0 < len(selected['entries']) <= 18
    assert sum(e['selected_file']['size'] for e in selected['entries']) < CAP
    data = {'schema_version': 'cold_truth.pexels_downloads.v1',
            'started_at_utc': datetime.now(timezone.utc).isoformat(),
            'selection': describe(SELECTION), 'maximum_new_media_bytes': CAP,
            'status': 'IN_PROGRESS', 'automatic_retry': False, 'entries': []}
    if resume:
        data = json.loads(RECEIPT.read_text(encoding='utf-8'))
        assert data['status'] == 'STOPPED_REQUIRES_RECONCILIATION'
        archived = HERE / 'archive/pexels_download_receipt_header_stop_2026_10_21.json'
        assert not archived.exists()
        archived.write_bytes(RECEIPT.read_bytes())
        data['manual_resume_after_header_review'] = {
            'at_utc': datetime.now(timezone.utc).isoformat(),
            'reason': 'Same Pexels video/file identity and URL verified again by getVideo. CDN Content-Length differs from API metadata by 5242 bytes. No file was written for the stopped response. Permit bounded actual CDN length; verify decoded media afterward.',
            'prior_checkpoint': describe(archived)}
        data['status'] = 'IN_PROGRESS'
    save(data)
    asset_root = ROOT / "Brody's Vault/2_IN_PRODUCTION/Amy Mihaljevic/Visuals/Longform/assets"
    for source in selected['entries']:
        dest = (ROOT / source['output_path']).resolve()
        assert dest.is_relative_to(asset_root.resolve())
        if dest.exists():
            completed = [entry for entry in data['entries'] if entry.get('status') == 'DOWNLOADED' and entry.get('output_path') == source['output_path']]
            assert resume and len(completed) == 1 and describe(dest) == completed[0]['output']
            continue
        url = source['selected_file']['link']
        assert urlparse(url).scheme == 'https' and urlparse(url).hostname == 'videos.pexels.com'
        assert source['selected_file']['width'] == 1920 and source['selected_file']['height'] == 1080
        expected = source['selected_file']['size']
        assert 0 < expected <= 150 * 1024 ** 2
        event = {'asset_id': source['asset_id'], 'source_identity': source['source_identity'],
                 'url': url, 'requested_at_utc': datetime.now(timezone.utc).isoformat(),
                 'expected_bytes': expected, 'output_path': source['output_path'], 'status': 'STARTED'}
        data['entries'].append(event)
        save(data)
        try:
            request = urllib.request.Request(url, headers={'User-Agent': 'ColdTruth-local-production/1.0'})
            with urllib.request.urlopen(request, timeout=60) as response:
                length = int(response.headers.get('Content-Length', '0'))
                assert 0 < length <= 150 * 1024 ** 2, f'Unbounded size for {dest.name}: {length}'
                event.update(cdn_content_length=length, api_size_differs=(length != expected))
                assert urlparse(response.url).hostname == 'videos.pexels.com'
                written = 0
                with dest.open('xb') as output:
                    while block := response.read(1024 ** 2):
                        written += len(block)
                        assert written <= length
                        assert sum(p.stat().st_size for p in asset_root.glob('*.mp4')) + len(block) < CAP
                        output.write(block)
            assert written == length
            event.update(status='DOWNLOADED', output=describe(dest), completed_at_utc=datetime.now(timezone.utc).isoformat())
            save(data)
            print(json.dumps({'downloaded': source['provider_id'], 'bytes': written}), flush=True)
        except Exception as error:
            event.update(status='FAILED_NO_RETRY', error_type=type(error).__name__, error=str(error))
            data['status'] = 'STOPPED_REQUIRES_RECONCILIATION'
            save(data)
            raise
    data.update(status='DOWNLOADS_COMPLETE_TECHNICAL_AND_RIGHTS_REVIEW_PENDING',
                completed_at_utc=datetime.now(timezone.utc).isoformat(),
                downloaded_bytes=sum(e['output']['bytes'] for e in data['entries'] if e.get('status') == 'DOWNLOADED'),
                video_rendered=False, assembly_allowed=False)
    save(data)

if __name__ == '__main__':
    main()

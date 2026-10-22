"""Open the installed GUI against the evaluated CPU runtime, without setup downloads.

This launcher does not grant further generation authority. The two-sample grant
is exhausted; use only for inspection/listening until Brody approves a new scope.
"""
import json
import os
import pathlib
import subprocess

root = pathlib.Path(__file__).resolve().parents[1]
trial = root / 'voice_samples/voicestudio_trial_01'
launch = json.loads((trial / 'backend_launch.json').read_text())
env = os.environ.copy()
env.update(launch['environment_overrides'])
env.update({
    'OMNIVOICE_BACKEND_CMD': json.dumps(launch['command']),
    'TEMP': str(trial / 'tmp'), 'TMP': str(trial / 'tmp'),
})
app = trial / 'app/VoiceStudio.exe'
assert app.is_file()
print('Opening the installed VoiceStudio GUI with the evaluated CPU runtime. No generation is submitted.')
raise SystemExit(subprocess.call([str(app), '--user-data-dir=' + str(trial / 'desktop-data')], env=env, creationflags=subprocess.CREATE_NO_WINDOW))

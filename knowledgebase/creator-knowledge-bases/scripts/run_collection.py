#!/usr/bin/env python3
"""Resume the confirmed 200-video collection with verified notebook recycling."""
import argparse
import json
import os
import subprocess
import sys
import time
from pathlib import Path

from import_notebooklm import ROOT


def run(script, *args):
    print(f'Running {script}', flush=True)
    subprocess.run([sys.executable, str(ROOT / 'scripts' / script), *args], cwd=ROOT, check=True)


def counts():
    total, imported, notes = 0, 0, 0
    for path in ROOT.glob('*/selection.json'):
        selected = set(json.loads(path.read_text())['videos'])
        total += len(selected)
        manifest = json.loads((path.parent / 'raw/manifest.json').read_text())
        imported += len(selected & {v['youtube_id'] for v in manifest['videos']})
        notes += sum((path.parent / 'scripts/extractions' / f'{key}.json').exists() for key in selected)
    return total, imported, notes


def alive(pid):
    if not pid:
        return False
    try:
        os.kill(pid, 0)
        status = Path(f'/proc/{pid}/status')
        if status.exists() and '\nState:\tZ' in status.read_text():
            return False
        return True
    except ProcessLookupError:
        return False


def checkpoint():
    run('replay.py')
    run('render.py')
    run('validate.py')
    run('recycle.py', '--execute')
    run('import_notebooklm.py', '--per-creator', '40')
    run('render.py')
    run('validate.py')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--wait-for-pid', type=int)
    args = parser.parse_args()
    worker = None
    pid = args.wait_for_pid
    passes = 0
    last_notes = -1
    while True:
        total, imported, notes = counts()
        if notes != last_notes:
            checkpoint()
            last_notes = counts()[2]
        if alive(pid):
            time.sleep(15)
            continue
        if worker:
            worker.wait()
        total, imported, notes = counts()
        if imported == notes == total:
            checkpoint()
            print('All selected transcripts and draft source notes saved. Editorial synthesis remains separate.', flush=True)
            return
        if passes >= 3:
            print(f'Automatic passes finished: {imported}/{total} transcripts; {notes}/{total} drafts. Inspect response errors.', flush=True)
            return
        checkpoint()
        size = [10, 5, 1][passes]
        passes += 1
        log = open(ROOT / f'extraction-auto-{passes}.log', 'a', buffering=1)
        worker = subprocess.Popen([sys.executable, str(ROOT / 'scripts/extract.py'), '--batch-size', str(size)], cwd=ROOT, stdout=log, stderr=subprocess.STDOUT)
        pid = worker.pid
        log.close()
        print(f'Extraction pass {passes}, batch size {size}, PID {pid}', flush=True)


if __name__ == '__main__':
    main()

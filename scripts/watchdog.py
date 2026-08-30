#!/usr/bin/env python3
import argparse, datetime, json, subprocess, time
from pathlib import Path

p = argparse.ArgumentParser()
p.add_argument('--unit', required=True)
p.add_argument('--state-dir', required=True)
p.add_argument('--reserve-gib', type=float, default=6.0)
p.add_argument('--max-swap-growth-mib', type=float, default=512.0)
a = p.parse_args()
unit = a.unit
state = Path(a.state_dir)
state.mkdir(parents=True, exist_ok=True)
reserve = int(a.reserve_gib * 1024**3)
max_swap_growth = int(a.max_swap_growth_mib * 1024**2)

def meminfo():
    out = {}
    for line in Path('/proc/meminfo').read_text().splitlines():
        key, val = line.split(':', 1)
        out[key] = int(val.strip().split()[0]) * 1024
    return out

def swap_used():
    m = meminfo()
    return m.get('SwapTotal', 0) - m.get('SwapFree', 0)

def show(prop):
    r = subprocess.run(['systemctl', '--user', 'show', unit, '-p', prop, '--value'], text=True, capture_output=True)
    return r.stdout.strip() if r.returncode == 0 else ''

for _ in range(180):
    if show('MainPID') not in ('', '0'):
        break
    if show('ActiveState') in ('failed', 'inactive'):
        raise SystemExit(0)
    time.sleep(1)

baseline = swap_used()
low_samples = 0
telemetry = state / 'watchdog-telemetry.jsonl'
with telemetry.open('a', buffering=1) as log:
    while True:
        active = show('ActiveState')
        pid = show('MainPID')
        if active not in ('active', 'activating') or pid in ('', '0'):
            break
        m = meminfo()
        available = m['MemAvailable']
        growth = max(0, swap_used() - baseline)
        low_samples = low_samples + 1 if available < reserve else 0
        row = {
            'at': datetime.datetime.now(datetime.timezone.utc).isoformat(),
            'unit': unit,
            'main_pid': int(pid),
            'mem_available_bytes': available,
            'swap_used_bytes': swap_used(),
            'swap_growth_bytes': growth,
            'reserve_bytes': reserve,
            'max_swap_growth_bytes': max_swap_growth,
        }
        log.write(json.dumps(row, sort_keys=True) + '\n')
        (state / 'watchdog-status.json').write_text(json.dumps(row, indent=2, sort_keys=True) + '\n')
        if low_samples >= 3 or growth > max_swap_growth:
            row['breach'] = 'reserve' if low_samples >= 3 else 'swap_growth'
            (state / 'watchdog-incident.json').write_text(json.dumps(row, indent=2, sort_keys=True) + '\n')
            subprocess.run(['systemctl', '--user', 'kill', '--kill-who=all', '--signal=SIGKILL', unit])
            raise SystemExit(2)
        time.sleep(2)

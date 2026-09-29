#!/usr/bin/env python3
"""Check that each game's record holds what the `match-series` capability
requires: the pairing, every turn's orders, the board after every turn, the
outcome and the final units in the log, and a history in JSON with one entry
per turn. Prints one line per game and exits non-zero if any is short."""

import json
import re
import sys
from pathlib import Path

LOGS = Path(__file__).resolve().parent / 'logs'


def check(gameno):
    log = LOGS / f'game_{gameno}.log'
    history = LOGS / f'game_{gameno}_history.json'
    problems = []
    if not log.exists():
        return [f'no log']
    text = log.read_text()
    if not re.search(r'^=== game \d+: p1 .+ vs p2 .+$', text, re.M):
        problems.append('no pairing line')
    if not re.search(r'^  board \d+x\d+, p1: \d+ points', text, re.M):
        problems.append('no board line')
    turns = [int(t) for t in re.findall(r'^  -- turn (\d+)$', text, re.M)]
    if not re.search(r'^  (game over|undecided after|not played)', text, re.M):
        problems.append('no outcome line')
    if 'final units:' not in text:
        problems.append('no final units')
    if not history.exists():
        problems.append('no history')
        return problems
    record = json.load(open(history))
    recorded = [entry['turn'] for entry in record['history']]
    expected = [1] + turns
    if recorded != expected:
        problems.append(f'history holds turns {recorded[:3]}..{recorded[-1:]}, '
                        f'log has {expected[:3]}..{expected[-1:]}')
    for entry in record['history']:
        if '+-+' not in entry['board'] or not entry['units']:
            problems.append(f'turn {entry["turn"]} has no board or units')
            break
    for turn in turns:
        block = text.split(f'  -- turn {turn}\n', 1)[1].split('\n', 2)
        if not (block[0].startswith('    p1: ') and block[1].startswith('    p2: ')):
            problems.append(f'turn {turn} has no orders for both seats')
            break
    return problems


def main(numbers):
    short = 0
    for gameno in numbers:
        problems = check(gameno)
        print(f'game {gameno}: ' + ('complete' if not problems
                                    else '; '.join(problems)))
        short += bool(problems)
    sys.exit(1 if short else 0)


if __name__ == '__main__':
    main([int(n) for n in sys.argv[1:]] or range(201, 221))

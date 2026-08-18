#!/usr/bin/env python3
"""Per-cell diff of two reports/canada_explorer.json payloads.

    python3 scripts/diff_explorer_cells.py OLD.json NEW.json [--min 1000]

Prints every (flow, commodity, year) whose value changed by more than --min,
grouped by commodity with the yearly deltas, plus commodities that appeared
or vanished. Snapshot the JSON BEFORE a change and read this before
believing any headline number."""
import json, sys, collections
old, new = json.load(open(sys.argv[1])), json.load(open(sys.argv[2]))
mn = 1000
if '--min' in sys.argv:
    mn = float(sys.argv[sys.argv.index('--min') + 1])
years = old['years']
def cells(d):
    out = {}
    for c in d['commodities']:
        for y, v in zip(d['years'], c['v']):
            if v is not None:
                out[(c['flow'], c['name'], y)] = v
    return out
O, N = cells(old), cells(new)
delta = collections.defaultdict(list)
for k in sorted(set(O) | set(N)):
    a, b = O.get(k), N.get(k)
    if (a or 0) == (b or 0):
        continue
    if abs((b or 0) - (a or 0)) < mn:
        continue
    delta[(k[0], k[1])].append((k[2], a, b))
up = down = 0
for (flow, name), lst in sorted(delta.items(), key=lambda kv: -sum(abs((b or 0)-(a or 0)) for _, a, b in kv[1])):
    tot = sum((b or 0) - (a or 0) for _, a, b in lst)
    print(f'{flow:9} {name[:48]:48} net {tot:+12,.0f}  ' +
          ' '.join(f'{y}:{(a or 0)/1e3:,.0f}k->{(b or 0)/1e3:,.0f}k' for y, a, b in lst[:8])
          + (' ...' if len(lst) > 8 else ''))
    up += sum(1 for _, a, b in lst if (b or 0) > (a or 0))
    down += sum(1 for _, a, b in lst if (b or 0) < (a or 0))
print(f'{len(delta)} commodities changed, {up} cells up, {down} cells down; '
      f'commodities {len(old["commodities"])} -> {len(new["commodities"])}')
on = {(c['flow'], c['name']) for c in old['commodities']}
nn = {(c['flow'], c['name']) for c in new['commodities']}
for k in sorted(nn - on): print('  NEW    ', k)
for k in sorted(on - nn): print('  GONE   ', k)

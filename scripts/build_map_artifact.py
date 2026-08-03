#!/usr/bin/env python3
"""Assemble the self-contained map artifact: inject map_slim.json + the
reconciliation known-issues into the HTML template."""
import json, csv
from pathlib import Path

slim = json.load(open('exports/map_slim.json'))
# land outlines (Natural Earth 110m, public domain) as lon/lat rings; the page
# projects them with the same px()/py() as the bubbles
slim['land'] = json.load(open('reference/world_land_110m.json'))
# The reconciliation report covers the whole payload, but the map only carries
# the curated whitelist, so roughly half its rows name a commodity the reader
# cannot open. Mark which ones are reachable ('m') instead of listing them all
# as if they were clickable. Regenerate the report AFTER any curation rename or
# these keys go stale - they did, and the issue chip silently stopped matching.
mapped = slim['commodities']
# The detector measures the RAW payload, so it still reports the parent/child
# double-count that build_map_slim resolves - it flagged raw cotton 1873 at
# 199% when the de-duplicated origins the reader sees reconcile at 1.00.
# Re-check each flag against the shipped figures and keep only what survives.
def resolved(name, year):
    e = mapped.get(name)
    if not e:
        return False
    t1 = (e.get('t1') or {}).get(str(year))
    nat = (e.get('nat') or {}).get(str(year))
    if not t1 or not nat or not nat[1]:
        return False
    return 0.85 <= nat[1] / t1 <= 1.15

issues, n_resolved = [], 0
for r in csv.DictReader(open('reports/country_t1_reconciliation.csv')):
    try:
        name, year = r['commodity'].strip(), int(r['year'])
        if resolved(name, year):
            n_resolved += 1
            continue
        issues.append({'c': name, 'y': year,
                       'kind': 'over' if r['kind'].startswith('over') else 'short',
                       'ratio': round(float(r['ratio']), 3),
                       'gbp': int(float(r['cluster_gbp'])),
                       'm': int(name in mapped)})
    except (ValueError, KeyError):
        continue
slim['resolved_issues'] = n_resolved
slim['issues'] = issues
blob = json.dumps(slim, ensure_ascii=False, separators=(',', ':'))
# safe inside <script type="application/json">: neutralise any '<'
blob = blob.replace('<', '\\u003c')

tmpl = Path('reference/trade_origins_map.template.html').read_text()
# the commodity count is quoted in the page's own prose - keep it honest,
# it read 1,235 for four weeks after the whitelist had moved on
tmpl = tmpl.replace('__NCOMM__', f"{len(slim['commodities']):,}")
html = tmpl.replace('/*__DATA__*/', blob)
out = Path('exports/trade_origins_map.html')
out.write_text(html)
n_m = sum(i['m'] for i in issues)
print(f'issues: {len(issues)} ({n_m} on commodities the map carries, '
      f'{n_resolved} already resolved by de-duplication)  '
      f'artifact: {out.stat().st_size/1e6:.2f} MB -> {out}')

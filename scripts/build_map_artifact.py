#!/usr/bin/env python3
"""Assemble the self-contained map artifact: inject map_slim.json + the
reconciliation known-issues into the HTML template."""
import json, csv
from pathlib import Path

slim = json.load(open('exports/map_slim.json'))
issues = []
for r in csv.DictReader(open('reports/country_t1_reconciliation.csv')):
    try:
        issues.append({'c': r['commodity'].strip(), 'y': int(r['year']),
                       'kind': 'over' if r['kind'].startswith('over') else 'short',
                       'ratio': round(float(r['ratio']), 3),
                       'gbp': int(float(r['cluster_gbp']))})
    except (ValueError, KeyError):
        continue
slim['issues'] = issues
blob = json.dumps(slim, ensure_ascii=False, separators=(',', ':'))
# safe inside <script type="application/json">: neutralise any '<'
blob = blob.replace('<', '\\u003c')

tmpl = Path('reference/trade_origins_map.template.html').read_text()
html = tmpl.replace('/*__DATA__*/', blob)
out = Path('exports/trade_origins_map.html')
out.write_text(html)
print(f'issues: {len(issues)}  artifact: {out.stat().st_size/1e6:.2f} MB -> {out}')

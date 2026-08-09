#!/usr/bin/env python3
"""Build the per-commodity QC dataset for a destination: series + defect flags.

The commodity axis of the export data has not had a curation pass, so a
composition table mixes real history with label events. This script produces
the series plus the flags that separate the two, so a human reading the small
multiples can adjudicate quickly.

Flags:
  zero_exit    present early, absent for the last >=3 years of the period
  zero_entry   absent early, present for the last stretch
  spike        one year >5x the mean of its neighbours (fused-digit signature)
  interior_gap missing years between a first and last observation
  low_proven   mean corroborated share < 40%
  rename_twin  another group whose observed years are nearly DISJOINT from this
               one and whose name shares >=40% of its tokens. That combination
               is the signature of a printed label changing (LINEN AND JUTE
               MANUFACTURES -> LINEN MANUFACTURES), which otherwise reads as one
               commodity dying and another being born in the same year.

The flags are heuristics for triage, not verdicts — a real commodity can
genuinely start or stop being traded. rename_twin in particular is a prompt to
look, not a finding.

Usage:
    python3 scripts/build_commodity_qc.py [--series reports/canada_export_series.csv]
                                          [--out reports/commodity_qc.json]
"""
import argparse, collections, csv, json, re, statistics


def norm(s):
    s = (s or '').lower()
    s = re.sub(r'&', ' and ', s)
    s = re.sub(r'[^a-z0-9]+', ' ', s)
    s = s.replace('em broidery', 'embroidery')
    s = re.sub(r'\b(unenumerated|unenum|erated|all other sorts|other sorts|'
               r'of all kinds|not otherwise described|etc|c)\b', ' ', s)
    return re.sub(r'\s+', ' ', s).strip()


STOP = {'and', 'of', 'or', 'the', 'not', 'in', 'for', 'other', 'all'}


def toks(s):
    return {t for t in norm(s).split() if t not in STOP and len(t) > 2}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--series', default='reports/canada_export_series.csv')
    ap.add_argument('--out', default='reports/commodity_qc.json')
    ap.add_argument('--top', type=int, default=40)
    a = ap.parse_args()

    rows = [r for r in csv.DictReader(open(a.series))
            if r['own_year'] == '1' and r['value']]
    years = sorted({int(r['year']) for r in rows})

    grp = collections.defaultdict(lambda: collections.defaultdict(float))
    tier = collections.defaultdict(collections.Counter)
    labels = collections.defaultdict(collections.Counter)
    for r in rows:
        g = norm(r['article_group']) or norm(r['article'])
        y, v = int(r['year']), float(r['value'])
        grp[g][y] += v
        tier[g][r['tier']] += 1
        labels[g][f"{r['article_group']} | {r['article']}"] += 1

    total = {g: sum(v.values()) for g, v in grp.items()}
    top = sorted(total, key=total.get, reverse=True)[:a.top]

    # rename twins: near-disjoint year coverage + shared name tokens
    twins = collections.defaultdict(list)
    for i, g1 in enumerate(top):
        for g2 in top[i + 1:]:
            y1, y2 = set(grp[g1]), set(grp[g2])
            if not y1 or not y2:
                continue
            overlap = len(y1 & y2) / min(len(y1), len(y2))
            t1, t2 = toks(g1), toks(g2)
            if not t1 or not t2:
                continue
            share = len(t1 & t2) / min(len(t1), len(t2))
            if overlap <= 0.15 and share >= 0.4:
                twins[g1].append(g2)
                twins[g2].append(g1)

    out = {'years': years, 'commodities': []}
    for g in top:
        s = grp[g]
        vals = [s.get(y) for y in years]
        obs = [y for y in years if y in s]
        first, last = obs[0], obs[-1]
        tail = [y for y in years if y >= years[-1] - 2]
        head = [y for y in years if y <= years[0] + 2]
        flags = []
        if last < years[-1] - 2 and any(y in s for y in head):
            flags.append('zero_exit')
        if first > years[0] + 2 and any(y in s for y in tail):
            flags.append('zero_entry')
        interior = [y for y in years if first < y < last and y not in s and y != 1871]
        if len(interior) >= 2:
            flags.append('interior_gap')
        for k, y in enumerate(obs):
            if 0 < k < len(obs) - 1:
                nb = (s[obs[k - 1]] + s[obs[k + 1]]) / 2
                if nb > 0 and s[y] / nb > 5:
                    flags.append('spike')
                    break
        n = sum(tier[g].values())
        good = tier[g]['A'] + tier[g]['B'] + tier[g]['C']
        prov = 100 * good / n if n else 0
        if prov < 40:
            flags.append('low_proven')
        if twins[g]:
            flags.append('rename_twin')
        out['commodities'].append({
            'name': g, 'total': round(total[g]), 'values': vals,
            'proven': round(prov), 'years_seen': len(obs), 'flags': flags,
            'twins': twins[g][:3],
            'labels': [k for k, _ in labels[g].most_common(4)]})

    out['commodities'].sort(key=lambda c: (-len(c['flags']), -c['total']))
    json.dump(out, open(a.out, 'w'), separators=(',', ':'))
    nf = sum(1 for c in out['commodities'] if c['flags'])
    print(f'commodity groups: {len(out["commodities"])} (top {a.top} by value)')
    print(f'  with at least one flag: {nf}')
    fc = collections.Counter(f for c in out['commodities'] for f in c['flags'])
    for f, k in fc.most_common():
        print(f'    {f:14} {k}')
    print(f'\nwrote {a.out}')


if __name__ == '__main__':
    main()

#!/usr/bin/env python3
"""Phase 5 step 2 of CANADA_IMPORTS_PLAN.md (workstream A1 of COMPLETION_PLAN.md): merge the
StatCan witness into the regime D staging corpus (FY1891-1897), block by block, arbitrated
by printed totals -- a VOTE, never pick-the-better-scan (user decision 2026-08-28).

    python3 scripts/ca_merge_regimeD.py [--dry-run]

Inputs  db/canada/imports_general_rows_d.csv      (Canadiana primary, ca_parse_regimeD.py)
        db/canada/imports_general_rows_d_w2.csv   (StatCan witness, ca_parse_regimeD.py --witness)
        reference/canada_printed_totals.csv       (the national room ledger, both value columns)
Output  db/canada/imports_general_rows_d.csv rewritten in place (old rows kept as row_kind
        'superseded_w2'), db/canada/witness_patches_d.csv (every decision),
        reports/canada_regimeD_merge.md.

A BLOCK is one article's run: its country rows (row_kind detail; province rows of a dash-
country run count as detail, their country_total does not) and its grand (article_total,
else the sum of its article_province_total rows).  Closure states:

    closed    sum(country rows) == grand within $1, in val_efc (and in val_imp when the
              grand carries one)
    mismatch  a grand exists and the country rows miss it
    no_total  no grand parsed -- the rows may still be complete

The vote, per (fy, section):

  * blocks pair by FINGERPRINT -- shared identical (country, val_efc) rows (>= 2, or half
    the smaller block), unique on both sides; then unique name equality (normalised);
  * a paired Canadiana block is REPLACED by the witness block only when the witness
    closes and Canadiana is provably worse: mismatch, or no_total with no more country-row
    mass than the closing witness;
  * an unpaired witness block INSERTS only when it closes, its article name is absent from
    Canadiana that year+section, and the national ledger has room in BOTH value columns
    (printed total minus the corpus so far, never exceeded by more than 1% of print);
  * everything else keeps Canadiana.

Row-level value fill (a Canadiana country row with a blank val_efc whose witness twin --
same article block pairing, same country -- carries one, with val_imp agreeing where both
exist) is applied to kept blocks.
"""
import csv, re, sys
from collections import defaultdict, Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from ca_check_abstract import ckey

ROOT = Path(__file__).resolve().parents[1]
ROWS = ROOT / 'db' / 'canada' / 'imports_general_rows_d.csv'
W2 = ROOT / 'db' / 'canada' / 'imports_general_rows_d_w2.csv'
PRINTED = ROOT / 'reference' / 'canada_printed_totals.csv'
ABS = ROOT / 'db' / 'canada' / 'imports_abstract_rows.csv'
PATCHES = ROOT / 'db' / 'canada' / 'witness_patches_d.csv'
OUT_MD = ROOT / 'reports' / 'canada_regimeD_merge.md'
ROOM_SLACK = 0.01
COUNTRY_SLACK = 0.01       # per-country room: abstract total x slack, floor $5,000
COUNTRY_FLOOR = 5000


def anorm(a):
    a = re.sub(r'[^a-z0-9 ]', ' ', (a or '').lower())
    return re.sub(r'\s+', ' ', a).strip()


def f(x):
    try: return float(x)
    except (TypeError, ValueError): return None


def load_blocks(path):
    """rows, {(fy, section): [block]} in file order."""
    rows = list(csv.DictReader(open(path)))
    groups = defaultdict(list)
    cur = None; key = None
    for idx, r in enumerate(rows):
        if r['row_kind'] in ('recap', 'section_total', 'heading_row', 'superseded_w2'):
            continue
        g = (r['fiscal_year'], r['section'] or '')
        k = (g, r['article'], r['table_seq'])   # a block never spans a table boundary (a new table
        # re-prints the article heading; consecutive same-article tables are re-joined below)
        if cur is None or (g, r['article']) != (key[0], key[1]):
            key = k
            cur = {'a': anorm(r['article']), 'name': r['article'], 'rows': [], 'det': [], 'tot': None,
                   'apt': 0.0, 'apt_i': 0.0, 'idx': []}
            groups[g].append(cur)
        cur['rows'].append(r); cur['idx'].append(idx)
        if r['row_kind'] == 'detail': cur['det'].append(r)
        elif r['row_kind'] == 'article_total': cur['tot'] = r
        elif r['row_kind'] == 'article_province_total':
            cur['apt'] += f(r['val_efc']) or 0; cur['apt_i'] += f(r['val_imp']) or 0
    for g, bs in groups.items():
        for b in bs:
            b['sum_e'] = sum(f(x['val_efc']) or 0 for x in b['det'])
            b['sum_i'] = sum(f(x['val_imp']) or 0 for x in b['det'])
            b['fp'] = {(ckey(x['country'] or ''), round(f(x['val_efc']) or 0)) for x in b['det']
                       if (x['country'] or '?') not in ('?', '') and f(x['val_efc'])}
            if b['tot'] is not None:
                tv_e, tv_i = f(b['tot']['val_efc']), f(b['tot']['val_imp'])
            elif b['apt']:
                tv_e, tv_i = b['apt'], (b['apt_i'] or None)
            else:
                tv_e = tv_i = None
            b['grand_e'], b['grand_i'] = tv_e, tv_i
            if tv_e is None or not b['det']:
                b['state'] = 'no_total'
            else:
                cols = ok = 0
                for tv, sv in ((tv_i, b['sum_i']), (tv_e, b['sum_e'])):
                    if not tv: continue
                    cols += 1
                    if abs(sv - tv) <= 1: ok += 1
                b['state'] = 'closed' if (cols and ok == cols) else ('mismatch' if cols else 'no_total')
    return rows, groups


def pair_blocks(b1, b2):
    used1 = set(); used2 = set(); pairs = []
    for j, w in enumerate(b2):
        if not w['fp']: continue
        best = []
        for i, c in enumerate(b1):
            if i in used1 or not c['fp']: continue
            shared = len(c['fp'] & w['fp'])
            need = max(2, min(len(c['fp']), len(w['fp'])) // 2)
            if shared >= need: best.append(i)
        if len(best) == 1:
            pairs.append((best[0], j)); used1.add(best[0]); used2.add(j)
    names1 = defaultdict(list)
    for i, c in enumerate(b1):
        if i not in used1 and c['a'] and c['a'] != '?': names1[c['a']].append(i)
    for j, w in enumerate(b2):
        if j in used2 or not w['a'] or w['a'] == '?': continue
        cand = [i for i in names1.get(w['a'], []) if i not in used1]
        if len(cand) == 1:
            pairs.append((cand[0], j)); used1.add(cand[0]); used2.add(j)
    return pairs, used1, used2


def main():
    dry = '--dry-run' in sys.argv
    rows, G1 = load_blocks(ROWS)
    wrows, G2 = load_blocks(W2)
    printed = {r['fiscal_year']: r for r in csv.DictReader(open(PRINTED))}

    # national ledger per fy: corpus detail mass vs printed, both columns
    mass = defaultdict(lambda: {'e': 0.0, 'i': 0.0})
    for r in rows:
        if r['row_kind'] == 'detail':
            mass[r['fiscal_year']]['e'] += f(r['val_efc']) or 0
            mass[r['fiscal_year']]['i'] += f(r['val_imp']) or 0
    before = {fy: dict(m) for fy, m in mass.items()}

    # per-country oracle: the volume's own Abstract by Countries and Provinces (ca_parse_abstract.py),
    # value entered for consumption summed over provinces; corpus mass per (fy, country)
    abs_c = defaultdict(lambda: defaultdict(float))
    for r in csv.DictReader(open(ABS)):
        if r['row_kind'] == 'province' and r['country'] != 'TOTAL' and r['fiscal_year'] in mass:
            abs_c[r['fiscal_year']][ckey(r['country'])] += f(r['efc_total']) or 0
    cmass = defaultdict(lambda: defaultdict(float))
    for r in rows:
        if r['row_kind'] == 'detail':
            cmass[r['fiscal_year']][ckey(r['country'] or '?')] += f(r['val_efc']) or 0
    cbefore = {fy: dict(m) for fy, m in cmass.items()}

    def block_country_mass(b):
        out = defaultdict(float)
        for x in b['det']:
            out[ckey(x['country'] or '?')] += f(x['val_efc']) or 0
        return out

    def country_room_ok(fy, add):
        """add: {country: delta efc}. Every touched country the abstract knows must stay within its
        printed total (+slack); a country the abstract does not list is judged by the national ledger only."""
        for c, d in add.items():
            if d <= 0 or c not in abs_c[fy]: continue
            lim = abs_c[fy][c] * (1 + COUNTRY_SLACK) + COUNTRY_FLOOR
            if cmass[fy][c] + d > lim: return False
        return True

    def apply_country(fy, add):
        for c, d in add.items(): cmass[fy][c] += d

    def room_ok(fy, add_e, add_i):
        pe = f(printed[fy]['entered_for_consumption']); pi = f(printed[fy]['total_imports'])
        ok_e = pe is None or mass[fy]['e'] + add_e <= pe * (1 + ROOM_SLACK)
        ok_i = pi is None or mass[fy]['i'] + add_i <= pi * (1 + ROOM_SLACK)
        return ok_e and ok_i

    patches = []
    replaced = inserted = filled = agreed = 0
    supersede = set()           # row indices in `rows` to mark superseded_w2
    duplicate = set()           # row indices of a block the OCR emitted twice in a row (FY1897 t124)
    for g, bs in G1.items():
        seen = set()
        for b in bs:
            sig = (b['rows'][0]['table_seq'], b['a'], tuple((ckey(x['country'] or ''), x['province'], x['val_efc']) for x in b['det']))
            if len(b['det']) >= 2 and sig in seen:       # the same article block twice in one table
                duplicate.update(b['idx'])
                mass[g[0]]['e'] -= b['sum_e']; mass[g[0]]['i'] -= b['sum_i']
                for k2, v2 in block_country_mass(b).items(): cmass[g[0]][k2] -= v2
                patches.append((g[0], g[1], b['name'], '', 'duplicate_block', b['state'], f'{b["sum_e"]:.0f}', 'dropped'))
            seen.add(sig)
    new_rows = defaultdict(list)  # insert-after index -> witness rows
    names_by_g = {g: {b['a'] for b in bs} for g, bs in G1.items()}
    stats = Counter()

    for g in sorted(set(G1) | set(G2)):
        b1, b2 = G1.get(g, []), G2.get(g, [])
        pairs, used1, used2 = pair_blocks(b1, b2)
        fy = g[0]
        for i, j in pairs:
            c, w = b1[i], b2[j]
            stats[('paired', c['state'], w['state'])] += 1
            if c['fp'] and c['fp'] == w['fp'] and abs(c['sum_e'] - w['sum_e']) <= 1:
                # two independent imagings read every country row identically: provenance, not a change
                for x in c['det']:
                    x['flags'] = (x['flags'] + ';' if x['flags'] else '') + 'witnessD_agree'
                agreed += 1
            superset = (w['state'] == 'no_total' and c['state'] == 'no_total' and c['fp'] and w['fp'] > c['fp']
                        and w['sum_e'] > c['sum_e'] + 1)      # the witness read every row Canadiana read, and more
            if (w['state'] == 'closed' and c['state'] != 'closed') or superset:
                worse = superset or c['state'] == 'mismatch' or (c['state'] == 'no_total' and c['sum_e'] <= w['sum_e'] + 1)
                if worse:
                    add_e = w['sum_e'] - c['sum_e']; add_i = w['sum_i'] - c['sum_i']
                    cadd = block_country_mass(w)
                    for k2, v2 in block_country_mass(c).items(): cadd[k2] -= v2
                    if room_ok(fy, add_e, add_i) and country_room_ok(fy, cadd):
                        apply_country(fy, cadd)
                        for k in c['idx']: supersede.add(k)
                        new_rows[c['idx'][-1]].extend(dict(x, flags=(x['flags'] + ';' if x['flags'] else '') + 'witnessD_block_replaced')
                                                      for x in w['rows'])
                        mass[fy]['e'] += add_e; mass[fy]['i'] += add_i
                        replaced += 1
                        patches.append((fy, g[1], c['name'], w['name'], 'replace' + ('_superset' if superset else ''), c['state'], f'{c["sum_e"]:.0f}->{w["sum_e"]:.0f}', 'accepted'))
                    else:
                        patches.append((fy, g[1], c['name'], w['name'], 'replace', c['state'], f'{c["sum_e"]:.0f}->{w["sum_e"]:.0f}', 'rejected: no room'))
                    continue
                patches.append((fy, g[1], c['name'], w['name'], 'replace', c['state'], f'{c["sum_e"]:.0f} vs {w["sum_e"]:.0f}', 'rejected: canadiana not provably worse'))
                continue
            # value fill on kept blocks: blank val_efc, witness twin by country
            if c['state'] != 'closed' and w['det']:
                wmap = defaultdict(list)
                for x in w['det']: wmap[(ckey(x['country'] or ''), x['province'])].append(x)
                for x in c['det']:
                    if f(x['val_efc']) is not None: continue
                    tw = wmap.get((ckey(x['country'] or ''), x['province']), [])
                    if len(tw) != 1 or f(tw[0]['val_efc']) is None: continue
                    if f(x['val_imp']) is not None and f(tw[0]['val_imp']) is not None and abs(f(x['val_imp']) - f(tw[0]['val_imp'])) > 1:
                        continue
                    if not room_ok(fy, f(tw[0]['val_efc']), 0): continue
                    x['val_efc'] = tw[0]['val_efc']
                    if f(x['val_imp']) is None and tw[0]['val_imp']: x['val_imp'] = tw[0]['val_imp']
                    if f(x['duty']) is None and tw[0]['duty']: x['duty'] = tw[0]['duty']
                    x['flags'] = (x['flags'] + ';' if x['flags'] else '') + 'witnessD_value_fill'
                    mass[fy]['e'] += f(tw[0]['val_efc']); cmass[fy][ckey(x['country'] or '?')] += f(tw[0]['val_efc']); filled += 1
                    patches.append((fy, g[1], c['name'], x['country'], 'fill', c['state'], tw[0]['val_efc'], 'accepted'))
        # unpaired witness blocks: insert whole articles Canadiana never read
        anchor = b1[-1]['idx'][-1] if b1 else None
        for j, w in enumerate(b2):
            if j in used2: continue
            stats[('unpaired', w['state'])] += 1
            if w['state'] != 'closed' or not w['a'] or w['a'] == '?':
                continue
            if w['a'] in names_by_g.get(g, set()):
                patches.append((fy, g[1], '', w['name'], 'insert', w['state'], f'{w["sum_e"]:.0f}', 'rejected: name present unpaired'))
                continue
            cadd = block_country_mass(w)
            if not room_ok(fy, w['sum_e'], w['sum_i']) or not country_room_ok(fy, cadd):
                patches.append((fy, g[1], '', w['name'], 'insert', w['state'], f'{w["sum_e"]:.0f}', 'rejected: no room'))
                continue
            if anchor is None:
                continue
            apply_country(fy, cadd)
            new_rows[anchor].extend(dict(x, flags=(x['flags'] + ';' if x['flags'] else '') + 'witnessD_block_inserted')
                                    for x in w['rows'])
            mass[fy]['e'] += w['sum_e']; mass[fy]['i'] += w['sum_i']
            inserted += 1
            patches.append((fy, g[1], '', w['name'], 'insert', w['state'], f'{w["sum_e"]:.0f}', 'accepted'))

    # write
    out = []
    for k, r in enumerate(rows):
        if k in duplicate:
            r = dict(r, row_kind='superseded_w2', flags=(r['flags'] + ';' if r['flags'] else '') + 'duplicate_block')
        elif k in supersede:
            r = dict(r, row_kind='superseded_w2', flags=(r['flags'] + ';' if r['flags'] else '') + 'superseded_by_witnessD')
        out.append(r)
        if k in new_rows:
            out.extend(new_rows[k])
    for n, r in enumerate(out):
        r['row_seq'] = n
    fields = list(rows[0].keys())
    if not dry:
        with open(ROWS, 'w', newline='') as fh:
            w = csv.DictWriter(fh, fieldnames=fields); w.writeheader(); w.writerows(out)
        with open(PATCHES, 'w', newline='') as fh:
            w = csv.writer(fh); w.writerow(['fiscal_year', 'section', 'canadiana_article', 'witness_article', 'op', 'canadiana_state', 'value', 'outcome'])
            w.writerows(patches)

    L = ['# Regime D witness merge (FY1891-1897)', '',
         f'blocks replaced {replaced}, inserted {inserted}, rows value-filled {filled}, blocks read identically by both witnesses {agreed}; {"DRY RUN" if dry else "written"}', '',
         '| FY | printed efc | before | ratio | after | ratio | printed imp | after imp | ratio |', '|---|---|---|---|---|---|---|---|---|']
    for fy in sorted(mass):
        pe = f(printed[fy]['entered_for_consumption']); pi = f(printed[fy]['total_imports'])
        L.append(f"| {fy} | {pe:,.0f} | {before[fy]['e']:,.0f} | {before[fy]['e']/pe:.3f} | {mass[fy]['e']:,.0f} | {mass[fy]['e']/pe:.3f} | "
                 f"{pi:,.0f} | {mass[fy]['i']:,.0f} | {mass[fy]['i']/pi:.3f} |")
    L += ['', '## Per-country check against the Abstract by Countries (val_efc)', '',
          '| FY | abstract Σ / print | corpus Σ / abstract | Great Britain | United States | biggest gaps (abstract - corpus) |', '|---|---|---|---|---|---|']
    for fy in sorted(mass):
        a = abs_c[fy]; d = cmass[fy]; pe = f(printed[fy]['entered_for_consumption'])
        gaps = sorted(((a.get(c, 0) - d.get(c, 0), c) for c in set(a) | set(d)), key=lambda t: -abs(t[0]))
        def rat(c):
            return f"{d.get(c, 0) / a[c]:.3f}" if a.get(c) else '-'
        L.append(f"| {fy} | {sum(a.values()) / pe:.4f} | {sum(d.get(c, 0) for c in a) / sum(a.values()):.3f} | {rat('great britain')} | {rat('united states')} | "
                 + '; '.join(f"{c[:22]} {g:+,.0f}" for g, c in gaps[:5]) + ' |')
    L += ['', 'Pairing outcomes (canadiana state, witness state): ' + ', '.join(f'{k}={v}' for k, v in sorted(stats.items(), key=lambda kv: -kv[1])[:16])]
    rej = Counter(p[7] for p in patches)
    L += ['', 'Decisions: ' + ', '.join(f'{k}={v}' for k, v in rej.most_common())]
    if not dry: OUT_MD.write_text('\n'.join(L) + '\n')
    print('\n'.join(L))


if __name__ == '__main__':
    main()

#!/usr/bin/env python3
"""Parse the 'No. 2 SUMMARY STATEMENT' of the Canadian Trade & Navigation volumes (regime C years):
article (x rate of duty) Dominion totals — quantity/value imported, quantity/value entered for home
consumption, duty.  This is the article-level Tier-1 for the General Statement: the sum of an
article's province rows over all countries must reproduce it.

Output: db/canada/imports_summary_rows.csv  (one row per printed line; row_kind article|subtotal|total)
"""
import csv, re, sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import ca_profile as P
import ca_parse_imports as I

OUT = P.ROOT / 'db' / 'canada' / 'imports_summary_rows.csv'
DITTO_ONLY = re.compile(r'^[\s“"”\'‘’,.]*$')


def split_heading(text):
    """Same parent/leaf split as the General Statement parser, returned as (parents, leaf)."""
    ctx = dict(article_parents=[], article=None, leaf_used=True)
    I.Parser._article(I.Parser(), ctx, text)
    return ctx.get('article_parents') or [], ctx.get('article')


def parse_volume(tag, fy, md_path, out):
    text = md_path.read_text(errors='replace')
    start = 0
    for mm in P.TN_START_RE2.finditer(text):
        if re.search(r'COMPILED\s+FROM\s+OFFICIAL\s+RETURNS', text[mm.start(): mm.start() + 1500], re.I):
            start = mm.start(); break
    tn = text[start:]
    pos = 0; in_sum = False; n = 0; diag = Counter()
    ctx = dict(section=None, parents=[], article=None, rate=None, buf=[])
    for seq, tm in enumerate(P.TABLE_RE.finditer(tn)):
        inter = tn[pos:tm.start()]; pos = tm.end()
        title = P.title_context(inter)[-300:]
        up = title.upper()
        if re.search(r'NO\.? ?2\.?\s*[—.-]?\s*SUMMARY STATEMENT', up) or (in_sum and re.search(r'SUMMARY STATEMENT', up)):
            in_sum = True
        elif re.search(r'NO\.? ?[3-9]\.?\s*[—.-]|COMPARATIVE|ABSTRACT|RECAPITULATION|GENERAL STATEMENT|EXPORT', up):
            in_sum = False
        if not in_sum:
            continue
        rows = P.parse_table(tm.group(0))
        hdr = ' '.join(c for r in rows if r and all(k == 'th' for k, _, _ in r) for _, _, c in r).upper()
        if hdr and 'ARTICLES' not in hdr and 'RATE' not in hdr and 'IMPORTED' not in hdr:
            continue
        body = [r for r in rows if r and not all(k == 'th' for k, _, _ in r)]
        modal = Counter(len(r) for r in body).most_common(1)[0][0] if body else 0
        if modal < 5 or modal > 9:
            diag['table_skipped_shape'] += 1; continue
        # a table whose first column is mostly numeric has lost its article column (scrambled page): skip
        if body and sum(1 for r in body if I.parse_num(r[0][2])[0] is not None) > len(body) / 2:
            diag['table_skipped_numeric_first_col'] += 1; continue
        # hallucinated generic headers ('Item | Unit | Quantity | Value', 'Item | 1883 | 1884') mark a scrambled page
        if body and re.match(r'^item\b', body[0][0][2].strip(), re.I):
            diag['table_skipped_hallucinated'] += 1; continue
        # a page whose rows repeat the same value pair across many columns is scrambled: skip the table
        def repeated(cells):
            nums = [I.parse_num(c)[0] for _, _, c in cells]
            nums = [v for v in nums if v is not None]
            return len(nums) >= 6 and any(all(nums[i] == nums[i % p] for i in range(len(nums))) for p in (1, 2, 3))
        if body and sum(1 for r in body if repeated(r)) > len(body) / 4:
            diag['table_skipped_repeated'] += 1; continue
        n += 1
        ctx['parents'] = []          # page tops repeat the group heading
        for cells in rows:
            if all(k == 'th' for k, _, _ in cells): continue
            texts = [c for _, _, c in cells]
            joined = ' '.join(texts)
            if re.search(r'^(DUTIABLE|FREE) GOODS', I.norm_label(texts[0]), re.I) or (len(texts) <= 2 and re.search(r'DUTIABLE|FREE GOODS', joined, re.I)):
                ctx['section'] = 'FREE' if re.search(r'FREE', joined, re.I) else 'DUTIABLE'
                ctx['parents'] = []; ctx['article'] = None
                if len(texts) <= 2: continue
                texts = [''] + texts[1:]
            # trailing empty cells shift the right-aligned values; a duty printed as two cells ('540,308 | 80')
            # is one cents-style cell
            while len(texts) > 2 and not texts[-1].strip():
                texts = texts[:-1]
            if len(texts) >= 3 and re.fullmatch(r'\d{2}', texts[-1].strip()) and re.fullmatch(r'[\d,]+', texts[-2].strip()):
                texts = texts[:-2] + [texts[-2].strip() + ' ' + texts[-1].strip()]
            if len(texts) < 5:
                continue
            # free goods carry no duty column (4 value cells); dutiable 5.  Decide per row: a trailing
            # cents-style cell ('1,234 56') or a 7+-cell row means 5 value cells.
            last = texts[-1].strip()
            five = (ctx['section'] != 'FREE') or len(texts) >= 7 or bool(re.search(r'\d \d\d$', last))
            NV = 5 if five else 4
            if len(texts) < NV + 1:
                continue
            vals = texts[-NV:]; labels = texts[:-NV]
            nums = [I.parse_num(v, cents_ok=(i == NV - 1)) for i, v in enumerate(vals)]
            if NV == 4:
                nums = nums + [(None, 'blank')]
            numeric = any(v is not None for v, f in nums)
            lab = labels[0] if labels else ''
            rate = labels[1] if len(labels) >= 2 else ''
            # ditto article (another rate line for the same article)
            if DITTO_ONLY.match(lab) and numeric:
                pass
            elif lab.strip():
                if not numeric:
                    frag = lab.strip()
                    if re.search(r'[—:;]\s*$', frag) or re.search(r'viz\.?\s*$', frag, re.I) or I.LEADER_RE.search(frag) and len(frag) > 4:
                        parents, leaf = split_heading(' '.join(ctx['buf'] + [frag]))
                        ctx['buf'] = []
                        if parents: ctx['parents'] = parents
                        ctx['article'] = leaf
                    else:
                        ctx['buf'].append(frag)
                    continue
                parents, leaf = split_heading(' '.join(ctx['buf'] + [lab]))
                ctx['buf'] = []
                if parents: ctx['parents'] = parents
                if leaf is not None: ctx['article'] = leaf
            if not numeric:
                continue
            kind = 'article'
            a = ctx['article'] or ''
            if re.match(r'(grand )?totals?\b', a, re.I) or re.match(r'(grand )?totals?\b', I.norm_label(lab), re.I) or ctx.get('recap'):
                kind = 'total'
            if re.match(r'(produce of the mine|total free goods)', a, re.I):
                kind = 'total'; ctx['recap'] = True      # the closing recapitulation by groups
            out.append(dict(fiscal_year=fy, volume=tag, table_seq=seq, section=ctx['section'],
                            article_parent=' > '.join(ctx['parents']), article=ctx['article'], rate=I.norm_label(rate),
                            row_kind=kind, qty_imp=nums[0][0], val_imp=nums[1][0], qty_efc=nums[2][0], val_efc=nums[3][0],
                            duty=nums[4][0], flags=','.join(f for v, f in nums if f and f != 'blank'), raw=' | '.join(texts)))
    return n, diag


def main():
    index = list(csv.DictReader(open(P.RAW / 'INDEX.tsv'), delimiter='\t'))
    out = []
    for row in index:
        tag = row['volume_tag']; fy = row['fiscal_year']
        if row.get('note', '').startswith('NOPARSE'): continue   # registered but pending its parser (INDEX.tsv note says which phase)
        md = P.RAW / tag / f'{tag}.md'
        if not md.exists(): continue
        before = len(out)
        n, diag = parse_volume(tag, fy, md, out)
        if n:
            v = sum(r['val_imp'] or 0 for r in out[before:] if r['row_kind'] == 'article')
            print(f'{fy:8} {tag:24} summary tables={n:3} rows={len(out)-before:5} sum val_imp={v:15,.0f}', file=sys.stderr)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    with open(OUT, 'w', newline='') as f:
        w = csv.DictWriter(f, fieldnames=list(out[0].keys())); w.writeheader()
        for r in out: w.writerow(r)
    print(f'wrote {OUT} ({len(out)} rows)', file=sys.stderr)


if __name__ == '__main__':
    main()

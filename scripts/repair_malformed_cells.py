#!/usr/bin/env python3
"""Cross-witness repair for malformed comma-group cells — the 1897-1900 fix.

detect_malformed_numbers.py found the mechanism: a comma-grouped figure at the
page edge loses digits (`39,94` for `40,904`), the parser strips commas and
stores 3,994 — an order of magnitude too small, silently. 92-95% of these sit
in the LAST numeric column of comparative volumes (as_1897/98/99 print ten
columns, five quantity + five value), which is why a volume's own year closes
worse than the years it reprints.

Repair is CROSS-WITNESS, not arithmetic:

  1. Match each malformed raw cell to the country_obs row storing the
     mis-parsed number (volume + value equality + country-label similarity —
     the same provenance-strict pattern as repair_fused_cells.py).
  2. Collect witnesses for that (flow, year, group, article, country) from
     OTHER volumes in country_obs, and from country_obs_inf (the second OCR
     engine, including its read of the SAME page — the page edge sometimes
     survives in one engine and not the other).
  3. Accept the modal witness value when two or more witnesses agree exactly,
     or a lone witness whose ratio to the bad value is consistent with the
     number of missing digits (a cell missing one digit must repair to
     roughly 10x itself, not to an arbitrary figure).
  4. A malformed cell with NO acceptable witness (1899/1900 edge cells when
     no engine read the page whole) is emitted with new_value BLANK — the
     consumers drop the cell rather than trust it. Detectable, not
     correctable: null it.

Only VALUE-column cells are repaired; malformed quantity cells are counted
and reported but the £ series never reads them.

Output feeds the same overlay mechanism as export_cell_repairs.csv (keyed on
the BAD value as well as the coordinates so a repair can only replace the
exact number it was derived from), in a separate file so either generator can
be re-run without clobbering the other.

Usage:
    python3 scripts/repair_malformed_cells.py [--volume as_1897] [--dry-run]
        [--out reference/malformed_cell_repairs.csv]
"""
import argparse, collections, csv, glob, html, os, re
import duckdb

ROW_RE = re.compile(r'<tr>(.*?)</tr>', re.S | re.I)
CELL_RE = re.compile(r'<td[^>]*>(.*?)</td>', re.S | re.I)
NUM_RE = re.compile(r'^-?\d{1,3}(?:,\d+)+$')


def clean(c):
    return re.sub(r'\s+', ' ', html.unescape(re.sub(r'<[^>]+>', ' ', c))).strip()


def malformed(s):
    if not NUM_RE.match(s):
        return False
    return any(len(g) != 3 for g in s.split(',')[1:])


def missing_digits(s):
    """Net digits lost: `39,94` -> 1, `1,23` -> 1, `1,2345` -> -1."""
    return sum(3 - len(g) for g in s.split(',')[1:])


def norm(s):
    return re.sub(r'[^A-Z0-9]', '', (s or '').upper())


def label_matches(label, country_raw):
    a, b = norm(label), norm(country_raw)
    if not a or not b:
        return False
    return a == b or a in b or b in a


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--db', default='db/uk_trade.duckdb')
    ap.add_argument('--raw', default='raw')
    ap.add_argument('--out', default='reference/malformed_cell_repairs.csv')
    ap.add_argument('--volume')
    ap.add_argument('--dry-run', action='store_true')
    a = ap.parse_args()

    con = duckdb.connect(a.db, read_only=True)

    # ------------------------------------------------------------------
    # 1. malformed raw cells, with the row's country label
    # ------------------------------------------------------------------
    cells = []          # (volume, label, raw_string, parsed_as)
    for d in sorted(glob.glob(f'{a.raw}/*')):
        if not os.path.isdir(d):
            continue
        vol = os.path.basename(d)
        if a.volume and vol != a.volume:
            continue
        md = glob.glob(f'{d}/**/*.md', recursive=True)
        if not md:
            continue
        text = open(md[0], encoding='utf-8', errors='replace').read()
        for rowhtml in ROW_RE.findall(text):
            row = [clean(c) for c in CELL_RE.findall(rowhtml)]
            label = row[0] if row else ''
            for c in row:
                if malformed(c):
                    cells.append((vol, label, c, int(c.replace(',', ''))))

    ingested = {v for (v,) in con.execute(
        'select distinct volume from country_obs').fetchall()}
    cells = [c for c in cells if c[0] in ingested]
    print(f'malformed raw cells in ingested volumes: {len(cells):,}')

    # ------------------------------------------------------------------
    # 2. match each to the country_obs row storing the mis-parsed number
    # ------------------------------------------------------------------
    matched, qty_only, unmatched, ambiguous, totals_skipped = [], 0, 0, 0, 0
    seen_keys = set()
    for vol, label, rawcell, parsed in cells:
        hits = con.execute("""
            select flow, year, article_group, article, country_raw, value
            from country_obs where volume = ? and value = ?
        """, [vol, float(parsed)]).fetchall()
        close = [h for h in hits if label_matches(label, h[4])]
        if not close and len(hits) == 1:
            close = hits                       # unique in the volume: take it
        if not close:
            # the malformed number went into the quantity column instead —
            # counted, not repaired: the £ series never reads quantity here
            if con.execute("""select count(*) from country_obs
                              where volume = ? and quantity = ?""",
                           [vol, float(parsed)]).fetchone()[0]:
                qty_only += 1
            else:
                unmatched += 1
            continue
        keys = {h[:5] for h in close}
        if len(keys) > 1:
            ambiguous += 1
            continue
        flow, yr, ag, art, ctry, val = close[0]
        # Subtotal rows are excluded: the printed hierarchy holds THREE 'TOTAL'
        # levels per section (Foreign, British Possessions, grand) that share
        # one (year, group, article, country) key, so witness voting cannot
        # tell them apart — the dry run repaired two different bad cells to
        # the same witness value, which is wrong for at least one of them.
        if 'TOTAL' in norm(ctry):
            totals_skipped += 1
            continue
        k = (vol, flow, yr, norm(ag), norm(art), norm(ctry), val)
        if k in seen_keys:
            continue                           # same defect found twice in raw
        seen_keys.add(k)
        matched.append(dict(volume=vol, flow=flow, year=yr,
                            article_group=ag or '', article=art or '',
                            country_raw=ctry, old_value=val,
                            raw_cell=rawcell,
                            d=missing_digits(rawcell)))

    print(f'matched to a country_obs VALUE cell : {len(matched):,}')
    print(f'subtotal (TOTAL) rows skipped       : {totals_skipped:,}')
    print(f'quantity-column cells (not repaired): {qty_only:,}')
    print(f'ambiguous (multiple rows match)     : {ambiguous:,}')
    print(f'not present in the DB               : {unmatched:,}')

    # ------------------------------------------------------------------
    # 3. witnesses: same (flow, year, group, article, country), other
    #    volumes in country_obs plus ALL volumes in country_obs_inf
    # ------------------------------------------------------------------
    def witnesses(m):
        rows = con.execute("""
            select 'obs:' || volume, value from country_obs
            where flow = ? and year = ? and volume <> ? and value is not null
              and regexp_replace(upper(coalesce(article_group,'')), '[^A-Z0-9]', '', 'g') = ?
              and regexp_replace(upper(coalesce(article,'')),       '[^A-Z0-9]', '', 'g') = ?
              and regexp_replace(upper(country_raw),                '[^A-Z0-9]', '', 'g') = ?
            union all
            select 'inf:' || volume, value from country_obs_inf
            where flow = ? and year = ? and value is not null
              and regexp_replace(upper(coalesce(article_group,'')), '[^A-Z0-9]', '', 'g') = ?
              and regexp_replace(upper(coalesce(article,'')),       '[^A-Z0-9]', '', 'g') = ?
              and regexp_replace(upper(country_raw),                '[^A-Z0-9]', '', 'g') = ?
        """, [m['flow'], m['year'], m['volume'],
              norm(m['article_group']), norm(m['article']), norm(m['country_raw']),
              m['flow'], m['year'],
              norm(m['article_group']), norm(m['article']), norm(m['country_raw'])]
        ).fetchall()
        # one vote per witness volume+engine — but a witness volume holding
        # two DIFFERENT values for the key (the fused-table collision class)
        # cannot tell us which row it means, so its vote is discarded
        byvol = collections.defaultdict(set)
        for wvol, v in rows:
            byvol[wvol].add(v)
        return {wvol: vs.pop() for wvol, vs in byvol.items() if len(vs) == 1}

    def section_exact(m):
        """Is the cell corroborated by its own printed page?

        A malformed comma group does not always mis-parse: `39,94` can be a
        misplaced comma on a printed `3,994`, in which case the stored value
        is RIGHT. The arbiter is the enclosing member section — if it closes
        exactly against its printed TOTAL with the current value in place,
        the compositor confirms the cell and it must be left alone. (The
        first run without this guard nulled correct cells and moved the
        closure metric DOWN.)
        """
        rows = con.execute("""
            select coalesce(unit,''), row_seq, country_raw, value
            from country_obs
            where volume = ? and flow = ? and year = ?
              and coalesce(article_group,'') = ? and coalesce(article,'') = ?
            order by coalesce(unit,''), row_seq
        """, [m['volume'], m['flow'], m['year'],
              m['article_group'], m['article']]).fetchall()
        byunit = collections.defaultdict(list)
        for unit, sq, ctry, v in rows:
            byunit[unit].append((ctry, v))
        for seq in byunit.values():
            members, has_cell = [], False
            for ctry, v in seq:
                if ctry and re.search(r'\bTOTAL\b', ctry, re.I):
                    if members and v is not None and has_cell and \
                            abs(sum(members) - v) <= 0.001 * abs(v):
                        return True
                    members, has_cell = [], False
                    continue
                if v is not None:
                    members.append(v)
                    if ctry == m['country_raw'] and v == m['old_value']:
                        has_cell = True
        return False

    def fingerprint_witnesses(m):
        """Find the witness row by its sibling-year VALUES, not its strings.

        The malformed row prints five year-columns; its other years are also
        in the DB under the same (volume, flow, group, article, country). A
        row in another volume that reproduces >= 2 of those year-values with
        no conflicting overlap is the same printed row, whatever it is
        spelled like, and its value for the malformed year is the witness.
        """
        sib = con.execute("""
            select year, value from country_obs
            where volume = ? and flow = ? and coalesce(article_group,'') = ?
              and coalesce(article,'') = ? and country_raw = ?
              and year <> ? and value is not null and value > 0
        """, [m['volume'], m['flow'], m['article_group'], m['article'],
              m['country_raw'], m['year']]).fetchall()
        if len(sib) < 2:
            return {}
        out = {}
        for eng, tbl in (('obs', 'country_obs'), ('inf', 'country_obs_inf')):
            cands = con.execute(f"""
                with sib(year, value) as (select * from (values {
                    ','.join(f'({y},{v})' for y, v in sib)}))
                select w.volume, coalesce(w.article_group,''),
                       coalesce(w.article,''), w.country_raw,
                       count(distinct w.year) as hits
                from {tbl} w join sib on w.year = sib.year and w.value = sib.value
                where w.flow = ? and w.volume <> ?
                group by 1,2,3,4 having hits >= 2
            """, [m['flow'], m['volume']]).fetchall()
            for wvol, ag, art, ctry, hits in cands:
                rows = con.execute(f"""
                    select year, value from {tbl}
                    where volume = ? and flow = ? and coalesce(article_group,'') = ?
                      and coalesce(article,'') = ? and country_raw = ?
                """, [wvol, m['flow'], ag, art, ctry]).fetchall()
                vals = collections.defaultdict(set)
                for y, v in vals_pairs(rows):
                    vals[y].add(v)
                # reject on any conflicting overlap year, or a doubled key
                if any(len(vals[y]) != 1 for y in vals):
                    continue
                if any(y in vals and v not in vals[y] for y, v in sib):
                    continue
                tgt = vals.get(m['year'])
                if tgt:
                    out[f'{eng}~{wvol}'] = tgt.copy().pop()
        return out

    def vals_pairs(rows):
        return [(y, v) for y, v in rows if v is not None]

    def ratio_ok(new, old, d):
        if old <= 0 or new <= 0 or new == old:
            return False
        r = new / old
        if d > 0:
            return 0.25 * 10 ** d <= r <= 4 * 10 ** d
        if d < 0:
            return 0.25 * 10 ** d <= r <= 4 * 10 ** d
        return False

    repairs, nulls, no_consensus = [], [], []
    page_confirmed = 0
    inf_same_page = collections.Counter()      # calibration: does the second
                                               # engine survive the page edge?
    for m in matched:
        if section_exact(m):
            page_confirmed += 1
            continue
        w = witnesses(m)
        inf_same = w.pop(f'inf:{m["volume"]}', None)
        votes = collections.Counter(w.values())
        best, n = (votes.most_common(1)[0] if votes else (None, 0))
        new = None
        if n >= 2 and best != m['old_value']:
            new = best
        elif n == 1 and ratio_ok(best, m['old_value'], m['d']):
            new = best
        if new is None:
            # STRING keys drift across volumes; the row's OTHER year-columns
            # are a fingerprint that finds the same printed row without
            # trusting spellings
            fw = fingerprint_witnesses(m)
            votes = collections.Counter(fw.values())
            best, n = (votes.most_common(1)[0] if votes else (None, 0))
            if n >= 2 and best != m['old_value']:
                new, w = best, fw
            elif n == 1 and ratio_ok(best, m['old_value'], m['d']):
                new, w = best, fw
        # NOTE: the second engine's read of the SAME page is deliberately NOT
        # admitted as a sole witness — calibration on cells with cross-volume
        # truth shows it agrees only ~1/3 of the time (the page edge is lost
        # in the scan, not in one OCR engine). 1899/1900 edge cells therefore
        # null out: detectable, not correctable.
        if new is not None and inf_same is not None:
            inf_same_page['agree' if inf_same == new else 'differ'] += 1
        rec = dict(volume=m['volume'], year=m['year'], flow=m['flow'],
                   article_group=m['article_group'], article=m['article'],
                   country_raw=m['country_raw'], old_value=m['old_value'],
                   new_value='' if new is None else new,
                   raw_cell=m['raw_cell'],
                   witnesses='; '.join(f'{k}={v:,.0f}' for k, v in sorted(w.items())))
        if new is not None:
            repairs.append(rec)
        elif not w and inf_same is None:
            nulls.append(rec)                  # no witness anywhere: drop it
        else:
            no_consensus.append(rec)           # witnesses exist but disagree /
                                               # fail the magnitude guard

    print(f'\npage-confirmed (exact section, kept): {page_confirmed:,}')
    print(f'repaired from witnesses             : {len(repairs):,}')
    print(f'no witness anywhere -> NULLED       : {len(nulls):,}')
    print(f'witnesses fail consensus (left as-is): {len(no_consensus):,}')
    print(f'second-engine same-page calibration : {dict(inf_same_page)}')

    byvy = collections.Counter((r['volume'], r['year']) for r in repairs)
    print('\nrepairs by volume/year:')
    for (v, y), n in sorted(byvy.items()):
        print(f'   {v} {y}: {n}')
    byvy = collections.Counter((r['volume'], r['year']) for r in nulls)
    if byvy:
        print('nulls by volume/year:')
        for (v, y), n in sorted(byvy.items()):
            print(f'   {v} {y}: {n}')

    print('\nlargest corrections:')
    for r in sorted(repairs, key=lambda r: -abs(float(r['new_value']) - r['old_value']))[:12]:
        print(f'  {r["volume"]} {r["year"]}  {r["old_value"]:>12,.0f} -> '
              f'{float(r["new_value"]):>12,.0f}  {r["country_raw"][:26]:26} '
              f'{r["article"][:32]}')

    if (repairs or nulls) and not a.dry_run:
        cols = ['volume', 'year', 'flow', 'article_group', 'article',
                'country_raw', 'old_value', 'new_value', 'raw_cell', 'witnesses']
        with open(a.out, 'w', newline='') as fh:
            wtr = csv.DictWriter(fh, fieldnames=cols)
            wtr.writeheader()
            wtr.writerows(repairs + nulls)
        print(f'\nwrote {a.out} ({len(repairs) + len(nulls)} rows, '
              f'{len(nulls)} of them null-outs)')


if __name__ == '__main__':
    main()

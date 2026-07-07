#!/usr/bin/env python3
"""Reconcile the two Tier 2 keys (country_obs = Chandra, country_obs_inf =
Infinity) block-by-block, arbitrated by the printed 'Total' rows and the
Tier 1 consensus, into country_consensus.

A block = one article's country rows ending at its printed Total. Per field
(quantity, value) the block resolves to:
  exact      — Chandra members already sum to the printed total
  inf_block  — Infinity's members do (Chandra slipped); adopt Infinity
  swap       — exactly one single-member (or total) substitution from the
               other engine makes the sum exact; adopt it
  anchor     — members sum to the Tier 1 consensus (tier A/B) national
               total for the article-year: the printed Total row itself
               was the misread; members kept
  nototal    — block has no printed Total (cannot check)
  flagged    — none of the above; keep Chandra, review queue

Every row records which engine (or repair) supplied each field.
"""
import re
import sys
import unicodedata
from collections import defaultdict
from pathlib import Path

import duckdb

BASE = Path('/home/jic823/uk_trade_db')


def norm(s):
    s = (s or '').replace('&amp;', '&')
    s = unicodedata.normalize('NFKD', s).encode('ascii', 'ignore').decode()
    s = s.lower().replace('&', ' and ')
    return re.sub(r'\s+', ' ', re.sub(r'[^a-z0-9]+', ' ', s)).strip()


def load_blocks(con, table):
    """-> {(vol, flow, duty, ng, na, year): block}; block = dict with
    members [(nc, raw_row)], total row or None, in reading order.

    Keyed by YEAR so the late-era 5-year layout (each country row carries 5
    year-columns, emitted as 5 records) forms one block per (article, year),
    matching the block-arithmetic model. Single-year volumes have a constant
    year per article, so this is equivalent to the old per-article block
    there. Page-continuation splits of one printed block auto-merge (same
    key); identical members from page overlap are de-duplicated."""
    rows = con.execute(f"""
        SELECT volume, flow, duty, article_group, article, country_raw,
               unit, year, quantity, value, consumption, duty_received
        FROM {table} ORDER BY volume, flow, duty, row_seq""").fetchall()
    blocks = {}
    seen = defaultdict(set)   # key -> {norm_country already added}
    for r in rows:
        vol, flow, duty, grp, art, ctry, unit, yr = r[:8]
        key = (vol, flow, duty, norm(grp), norm(art), yr)
        blk = blocks.get(key)
        if blk is None:
            blk = blocks[key] = {'members': [], 'total': None,
                                 'grp': grp, 'art': art}
        if ctry == 'TOTAL':
            if blk['total'] is None:
                blk['total'] = r
        else:
            nc = norm(ctry)
            if nc in seen[key]:
                continue          # page-overlap duplicate of same country
            seen[key].add(nc)
            blk['members'].append((nc, r))
    return blocks


def field_sum(members, idx):
    s = 0.0
    n = 0
    for nc, r in members:
        if ' : ' in (r[5] or ''):
            continue                     # port breakdown under a country row
        if r[idx] is not None:
            s += r[idx]
            n += 1
    return s, n


def resolve_field(ch_members, ch_total, inf_by_c, inf_total, anchor, idx):
    """-> (status, {norm_country: adopted_value or None}, total_value)."""
    vals = {nc: r[idx] for nc, r in ch_members}
    tot = ch_total[idx] if ch_total is not None else None
    s, n = field_sum(ch_members, idx)
    if tot is None:
        return ('nototal', vals, None) if n else ('empty', vals, None)
    if n >= 2 and abs(s - tot) < 0.5:
        return 'exact', vals, tot
    # whole-block Infinity
    if inf_by_c:
        i_s = i_n = 0
        ivals = {}
        for nc, r in ch_members:
            iv = inf_by_c.get(nc)
            v = iv[idx] if iv else None
            ivals[nc] = v
            if v is not None and ' : ' not in (r[5] or ''):
                i_s += v
                i_n += 1
        for t in (tot, inf_total[idx] if inf_total is not None else None):
            if t is not None and i_n >= 2 and abs(i_s - t) < 0.5:
                return 'inf_block', ivals, t
        # single-member swap
        hits = []
        for nc, r in ch_members:
            iv = inf_by_c.get(nc)
            if not iv or iv[idx] is None or r[idx] is None \
                    or abs(iv[idx] - r[idx]) < 0.5 \
                    or ' : ' in (r[5] or ''):
                continue
            if abs(s - r[idx] + iv[idx] - tot) < 0.5:
                hits.append((nc, iv[idx]))
        if len(hits) == 1:
            out = dict(vals)
            out[hits[0][0]] = hits[0][1]
            return 'swap', out, tot
        # total swap: members already sum to the OTHER engine's total
        if inf_total is not None and inf_total[idx] is not None \
                and n >= 2 and abs(s - inf_total[idx]) < 0.5:
            return 'swap', vals, inf_total[idx]
    # consensus anchor: members sum to the tier-A/B national total
    if anchor is not None and n >= 2 and abs(s - anchor) < 0.5:
        return 'anchor', vals, s
    # constrained digit repair: the printed total is independently
    # confirmed (other engine or tier-A/B anchor reads the same), and
    # exactly ONE member admits a single-digit change equal to the residual
    # (first-digit slips dominate the validated OCR error profile)
    tot_confirmed = (
        (inf_total is not None and inf_total[idx] is not None
         and abs(inf_total[idx] - tot) < 0.5)
        or (anchor is not None and abs(anchor - tot) < 0.5))
    if tot_confirmed and n >= 2:
        delta = tot - s
        hits = []
        for nc, r in ch_members:
            v = r[idx]
            if v is None or ' : ' in (r[5] or ''):
                continue
            f = v + delta
            if f > 0 and _one_digit_apart(v, f):
                hits.append((nc, f))
        if len(hits) == 1:
            out = dict(vals)
            out[hits[0][0]] = hits[0][1]
            return 'digit_fix', out, tot
    # near = one small slip somewhere (usable when magnitude is what
    # matters); flagged = structural, members may be wrong/missing
    if tot > 0 and abs(s - tot) / tot < 0.02:
        return 'near', vals, tot
    return 'flagged', vals, tot


def _one_digit_apart(a, b):
    sa, sb = f'{a:.0f}', f'{b:.0f}'
    return (len(sa) == len(sb)
            and sum(x != y for x, y in zip(sa, sb)) == 1)


def match_blocks(ch, inf):
    """Pair engine blocks: exact key first, then content fingerprints —
    engines drift on article labels/occurrence counts, but the member
    VALUES mostly agree, so shared values identify the same printed block.
    Returns {ch_key: inf_key}."""
    pairs = {}
    used = set()
    for k in ch:
        if k in inf:
            pairs[k] = k
            used.add(k)
    # index unmatched inf blocks by their member values (per volume+flow)
    val_index = defaultdict(list)
    for ik, blk in inf.items():
        if ik in used:
            continue
        for nc, r in blk['members']:
            for idx in (8, 9):
                v = r[idx]
                if v is not None and v >= 100:   # small values collide
                    val_index[(ik[0], ik[1], ik[5], v)].append(ik)
    n_content = 0
    for k, blk in ch.items():
        if k in pairs:
            continue
        votes = defaultdict(int)
        n_vals = 0
        for nc, r in blk['members']:
            for idx in (8, 9):
                v = r[idx]
                if v is not None and v >= 100:
                    n_vals += 1
                    for ik in val_index.get((k[0], k[1], k[5], v), ()):
                        votes[ik] += 1
        if not votes or n_vals < 2:
            continue
        best, bv = max(votes.items(), key=lambda x: x[1])
        if best in used or bv < max(2, 0.4 * n_vals):
            continue
        pairs[k] = best
        used.add(best)
        n_content += 1
    print(f'  content-matched {n_content:,} more blocks')
    return pairs


def align_members(ch_blk, inf_blk):
    """{ch_norm_country: inf_row} — by country name, leftovers by order."""
    out = {}
    inf_left = list(inf_blk['members'])
    by_c = {}
    for nc, r in inf_blk['members']:
        by_c.setdefault(nc, r)
    ch_left = []
    for nc, r in ch_blk['members']:
        if nc in by_c:
            out[nc] = by_c[nc]
            inf_left = [(inc, ir) for inc, ir in inf_left if inc != nc]
        else:
            ch_left.append(nc)
    for nc, (inc, ir) in zip(ch_left, inf_left):
        out[nc] = ir
    return out


def self_ok(blk, idx):
    """Block's own members sum to its own printed total."""
    if blk['total'] is None or blk['total'][idx] is None:
        return False
    s, n = field_sum(blk['members'], idx)
    return n >= 2 and abs(s - blk['total'][idx]) < 0.5


def main():
    con = duckdb.connect(str(BASE / 'db' / 'uk_trade.duckdb'))
    ch = load_blocks(con, 'country_obs')
    inf = load_blocks(con, 'country_obs_inf')
    print(f'blocks: chandra {len(ch):,}  infinity {len(inf):,}  '
          f'key-matched {sum(1 for k in ch if k in inf):,}')
    pairs = match_blocks(ch, inf)

    # Tier 1 consensus anchors: (flow, measure, name-norm, year) -> value
    anchors = {}
    for flow, meas, grp, art, y, v, tier in con.execute("""
            SELECT flow, measure, article_group, article, year, value, tier
            FROM consensus WHERE tier IN ('A','B')""").fetchall():
        for nk in (norm(f'{grp} {art}' if grp else art), norm(art)):
            anchors.setdefault((flow, meas, nk, y), v)

    con.execute('DROP TABLE IF EXISTS country_consensus')
    con.execute('''CREATE TABLE country_consensus (
        volume VARCHAR, flow VARCHAR, duty VARCHAR,
        article_group VARCHAR, article VARCHAR, country_raw VARCHAR,
        unit VARCHAR, year INTEGER, quantity DOUBLE, value DOUBLE,
        q_block VARCHAR, v_block VARCHAR,
        q_cell VARCHAR, v_cell VARCHAR, row_seq INTEGER)''')

    stats = {'quantity': defaultdict(int), 'value': defaultdict(int)}
    ins = []
    seq = 0
    def emit_block(vol, flow, duty, blk, q_st, v_st, q_vals=None,
                   v_vals=None, q_tot=None, v_tot=None, inf_by_c=None):
        nonlocal seq

        def cell(r, nc, idx, vals):
            final = vals.get(nc, r[idx]) if vals else r[idx]
            if final is None:
                return None, 'empty'
            if vals and r[idx] is not None and abs(final - r[idx]) >= 0.5:
                return final, 'repaired'
            ir = inf_by_c.get(nc) if inf_by_c else None
            if ir is None or ir[idx] is None:
                return final, 'single'
            return final, ('agree' if abs(final - ir[idx]) < 0.5
                           else 'differ')

        for nc, r in blk['members']:
            seq += 1
            q, q_c = cell(r, nc, 8, q_vals)
            v, v_c = cell(r, nc, 9, v_vals)
            ins.append([vol, flow, duty, r[3], r[4], r[5], r[6], r[7],
                        q, v, q_st, v_st, q_c, v_c, seq])
        if blk['total'] is not None:
            t = blk['total']
            seq += 1
            ins.append([vol, flow, duty, t[3], t[4], 'TOTAL', t[6], t[7],
                        q_tot if q_tot is not None else t[8],
                        v_tot if v_tot is not None else t[9],
                        q_st, v_st, 'total', 'total', seq])

    for k, blk in ch.items():
        vol, flow, duty, ng, na, occ = k
        iblk = inf.get(pairs.get(k))
        # if Infinity's version of the block is arithmetically self-
        # consistent on more fields than Chandra's, Chandra broke the
        # STRUCTURE (dropped/merged a member) — adopt Infinity's block
        ch_score = self_ok(blk, 8) + self_ok(blk, 9)
        # never adopt Infinity structure for a members-less Chandra block:
        # a grand-total row (the print splits foreign/British/grand) would
        # pull in Infinity's copy of member rows already emitted from the
        # component blocks — double-counting them
        if iblk and len(blk['members']) >= 2:
            inf_score = self_ok(iblk, 8) + self_ok(iblk, 9)
            if inf_score > ch_score:
                q_st = 'inf_struct' if self_ok(iblk, 8) else (
                    'nototal' if iblk['total'] is None
                    or iblk['total'][8] is None else 'flagged')
                v_st = 'inf_struct' if self_ok(iblk, 9) else (
                    'nototal' if iblk['total'] is None
                    or iblk['total'][9] is None else 'flagged')
                stats['quantity'][q_st] += 1
                stats['value'][v_st] += 1
                emit_block(vol, flow, duty, iblk, q_st, v_st)
                continue
        inf_by_c = align_members(blk, iblk) if iblk else {}
        year = blk['members'][0][1][7] if blk['members'] else \
            (blk['total'][7] if blk['total'] is not None else None)
        res = {}
        for field, idx, meas in (('quantity', 8, 'quantity'),
                                 ('value', 9, 'value')):
            anchor = None
            for nk in (norm(f"{blk['grp']} {blk['art']}"
                            if blk['art'] else blk['grp']),
                       norm(blk['art'] or blk['grp'])):
                anchor = anchors.get((flow, meas, nk, year))
                if anchor is not None:
                    break
            st, vals, tot = resolve_field(
                blk['members'], blk['total'], inf_by_c,
                iblk['total'] if iblk else None, anchor, idx)
            stats[field][st] += 1
            res[field] = (st, vals, tot)
        emit_block(vol, flow, duty, blk, res['quantity'][0], res['value'][0],
                   res['quantity'][1], res['value'][1],
                   res['quantity'][2], res['value'][2], inf_by_c=inf_by_c)

    # Infinity-only blocks: self-consistent blocks for articles Chandra
    # missed entirely (conservative: only when no ch block shares the
    # article key, so nothing double-counts)
    used_inf = set(pairs.values())
    ch_art_keys = {(k[0], k[1], k[2], k[3], k[4]) for k in ch}
    n_inf_only = 0
    for ik, iblk in inf.items():
        if ik in used_inf or (ik[0], ik[1], ik[2], ik[3], ik[4]) in ch_art_keys:
            continue
        if not (self_ok(iblk, 8) or self_ok(iblk, 9)):
            continue
        q_st = 'inf_only' if self_ok(iblk, 8) else 'nototal'
        v_st = 'inf_only' if self_ok(iblk, 9) else 'nototal'
        stats['quantity'][q_st] += 1
        stats['value'][v_st] += 1
        emit_block(ik[0], ik[1], ik[2], iblk, q_st, v_st)
        n_inf_only += 1
    print(f'infinity-only self-consistent blocks added: {n_inf_only:,}')
    import pandas as pd
    cdf = pd.DataFrame(ins, columns=[
        'volume', 'flow', 'duty', 'article_group', 'article', 'country_raw',
        'unit', 'year', 'quantity', 'value', 'q_block', 'v_block', 'q_cell',
        'v_cell', 'row_seq'])
    con.execute('INSERT INTO country_consensus SELECT * FROM cdf')
    con.commit()

    print(f'country_consensus rows: {len(ins):,}')
    for field in ('quantity', 'value'):
        st = stats[field]
        checkable = sum(v for s, v in st.items()
                        if s not in ('nototal', 'empty'))
        good = (st['exact'] + st['inf_block'] + st['swap'] + st['anchor']
                + st['inf_struct'] + st['inf_only'] + st['digit_fix'])
        print(f'{field}: blocks checkable {checkable:,} — '
              f'exact {st["exact"]:,}, inf_struct {st["inf_struct"]:,}, '
              f'inf_block {st["inf_block"]:,}, swap {st["swap"]:,}, '
              f'anchor {st["anchor"]:,}, inf_only {st["inf_only"]:,}, '
              f'digit_fix {st["digit_fix"]:,}, near {st["near"]:,}, '
              f'flagged {st["flagged"]:,}  '
              f'-> verified {good / max(checkable, 1):.1%}, '
              f'+near {(good + st["near"]) / max(checkable, 1):.1%}')


if __name__ == '__main__':
    main()

#!/usr/bin/env python3
"""Loader for reference/inf_fallback_rows.csv (build_inf_fallback.py): whole
sections the primary engine never read, taken from country_obs_inf where
they close on their printed TOTAL. Consumers append these to the rows they
fetch from country_obs, in the same column order, BEFORE overlays/relabels."""
import csv, os

PATH = 'reference/inf_fallback_rows.csv'


def load_rows(flow, path=PATH, with_qty=False):
    """-> [(volume, flow, year, article_group, article, unit, row_seq,
    country_raw, value[, quantity=None])] for one flow; [] if absent."""
    if not os.path.exists(path):
        return []
    out = []
    for r in csv.DictReader(open(path)):
        if r['flow'] != flow:
            continue
        t = (r['volume'], r['flow'], int(r['year']), r['article_group'] or '',
             r['article'] or None, r['unit'] or None, int(r['row_seq']),
             r['country_raw'], float(r['value']) if r['value'] != '' else None)
        out.append(t + (None,) if with_qty else t)
    return out

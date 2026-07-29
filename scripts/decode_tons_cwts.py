"""Decode the fused 'Tons. Cwts' quantity column, block by block, and verify
each block against its OWN printed totals. Emit nothing that does not close."""
import duckdb, itertools, sys

c = duckdb.connect('/home/jic823/uk_trade_db/db/uk_trade.duckdb', read_only=True)

def cands(n):
    """(tons, cwts) readings of a fused figure; cwts must be 0..19."""
    out = []
    for w in (2, 1):
        t, cw = n // (10 ** w), n % (10 ** w)
        if cw <= 19 and t > 0:
            out.append((t, cw))
    out.append((n, 0))                     # no cwt digits fused at all
    seen, uniq = set(), []
    for x in out:
        if x not in seen:
            seen.add(x); uniq.append(x)
    return uniq

def tc(t, cw):          # to twentieths of a ton, so carrying is exact
    return t * 20 + cw

blocks = c.execute("""SELECT DISTINCT volume, article_group, article
    FROM country_obs WHERE unit='Tons. Cwts' AND flow='import'
    ORDER BY volume""").fetchall()

for vol, g, a in blocks:
    rows = c.execute("""SELECT row_seq, country_raw, quantity, value FROM country_obs
        WHERE volume=? AND article_group=? AND article=? AND unit='Tons. Cwts'
        ORDER BY row_seq""", [vol, g, a]).fetchall()
    rows = [r for r in rows if r[2] is not None]
    mem = [r for r in rows if not (r[1] or '').upper().startswith('TOTAL')]
    tot = [r for r in rows if (r[1] or '').upper().startswith('TOTAL')]
    if not tot or not mem:
        print(f'{vol} {a[:30]!r}: SKIP (no printed total / no members)'); continue
    grand = int(tot[-1][2])
    # the members must sum (with cwt carrying) to one of the grand's readings,
    # MINUS the British half if the block has two sub-totals
    targets = []
    for gt, gcw in cands(grand):
        if len(tot) >= 3:                  # foreign / british / grand
            for ft, fcw in cands(int(tot[0][2])):
                targets.append(('foreign', tc(ft, fcw), (gt, gcw)))
        targets.append(('grand', tc(gt, gcw), (gt, gcw)))
    opts = [cands(int(r[2])) for r in mem]
    n = 1
    for o in opts:
        n *= len(o)
    if n > 400000:
        print(f'{vol} {a[:30]!r}: SKIP (search space {n:,})'); continue
    hits = []
    for combo in itertools.product(*opts):
        s = sum(tc(t, cw) for t, cw in combo)
        for kind, target, gread in targets:
            if s == target:
                hits.append((combo, kind, target, gread))
                break
    # a subset-sum that closes is only evidence if it is the ONLY one
    hit = hits[0] if hits else None
    if len(hits) > 1:
        print(f'{vol} {a[:34]!r}: {len(hits)} DISTINCT decodes close - AMBIGUOUS')
        for h in hits[:4]:
            print('     ', [f'{t}t{cw}' for t, cw in h[0]], '->', h[1])
        continue
    if not hit:
        print(f'{vol} {a[:30]!r}: NO EXACT DECODE (grand {grand:,})'); continue
    combo, kind, target, gread = hit
    print(f'{vol} {a[:34]!r} CLOSES on the printed {kind} total '
          f'({target//20}t {target%20}cwt); grand reads {gread[0]}t {gread[1]}cwt')
    for r, (t, cw) in zip(mem, combo):
        px = r[3] / (t + cw / 20) if (t or cw) else 0
        print(f'    {r[1][:32]:32} {int(r[2]):>10,} -> {t:>6,}t {cw:>2}cwt  '
              f'GBP{r[3] or 0:>9,.0f}  px={px:7.1f}')

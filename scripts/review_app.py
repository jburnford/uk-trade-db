#!/usr/bin/env python3
"""Human review interface for the country_review_queue: shows the EXACT
scanned page next to each grade-C cell, records confirm/correct decisions.

  python3 scripts/review_app.py [port]        (default 8077)
  -> http://localhost:8077

Queue rows ranked by GBP exposure (capped); filters for wood / Canada.
Decisions append to reference/human_review.csv, which grade_country.py
applies on its next run (confirmed/corrected cells become grade A with
cell status 'human'; junk rows are excluded from exports).

Stdlib only (http.server); page images rendered on demand with pdftoppm
into page_cache/. PDFs live in pdfs/ (synced from nibi chandra2/input).
"""
import csv
import html
import json
import subprocess
import sys
import urllib.parse
from datetime import datetime
from http.server import HTTPServer, BaseHTTPRequestHandler
from pathlib import Path

BASE = Path('/home/jic823/uk_trade_db')
QUEUE = BASE / 'reports' / 'country_review_queue.csv'
PAGES = BASE / 'reports' / 'review_pages.json'
DECISIONS = BASE / 'reference' / 'human_review.csv'
PDFS = BASE / 'pdfs'
CACHE = BASE / 'page_cache'
CEILING = 50_000_000

CACHE.mkdir(exist_ok=True)


def row_key(r):
    return '|'.join([r['volume'], r['flow'], r['duty'] or '', r['group'],
                     r['article'] or '', r['country'], str(r['year'])])


def load_state():
    rows = list(csv.DictReader(open(QUEUE)))
    pages = json.load(open(PAGES)) if PAGES.exists() else {}
    done = {}
    if DECISIONS.exists():
        for d in csv.DictReader(open(DECISIONS)):
            done[d['key']] = d
    # rank by GBP exposure; over-ceiling values are placement junk whose
    # true magnitude is unknown — park them at the bottom
    def exposure(r):
        try:
            v = float(r['value'] or 0)
        except ValueError:
            v = 0
        return v if v <= CEILING else -1
    rows.sort(key=lambda r: -exposure(r))
    return rows, pages, done


def is_wood(r):
    g = (r['group'] or '').lower()
    return 'wood' in g and 'timber' in g


def esc(s):
    return html.escape(str(s if s is not None else ''))


STYLE = """<style>
body{font-family:system-ui,sans-serif;margin:0;display:flex;height:100vh}
#side{width:430px;overflow-y:auto;padding:14px;border-right:1px solid #ccc}
#main{flex:1;overflow:auto;background:#444;text-align:center}
#main img{width:100%;height:auto}
table{border-collapse:collapse;font-size:13px;margin:8px 0}
td,th{border:1px solid #ddd;padding:3px 7px;text-align:left}
.k{color:#666}.v{font-weight:600}
button{margin:3px;padding:7px 13px;cursor:pointer;border-radius:4px;
border:1px solid #888}
.confirm{background:#c9efc9}.junk{background:#f2c9c9}
.nf{background:#eee}
input[type=text]{width:110px;padding:4px}
a{color:#1a56a0}.done{color:#2b7a2b;font-weight:600}
.filter a{margin-right:10px}
.badge{font-size:11px;background:#eee;border-radius:3px;padding:1px 5px}
</style>"""


def page_png(pdf_stem, page):
    """Render page (1-based) to cached PNG; return path or None."""
    out = CACHE / f'{pdf_stem}_{page}.png'
    if out.exists():
        return out
    pdf = PDFS / f'{pdf_stem}.pdf'
    if not pdf.exists():
        return None
    subprocess.run(['pdftoppm', '-f', str(page), '-l', str(page),
                    '-r', '150', '-png', '-singlefile',
                    str(pdf), str(out.with_suffix(''))], check=False,
                   timeout=120)
    return out if out.exists() else None


class H(BaseHTTPRequestHandler):
    def log_message(self, *a):
        pass

    def send_html(self, body, code=200):
        b = ('<!doctype html><meta charset="utf-8">' + STYLE
             + body).encode()
        self.send_response(code)
        self.send_header('Content-Type', 'text/html; charset=utf-8')
        self.send_header('Content-Length', str(len(b)))
        self.end_headers()
        self.wfile.write(b)

    def do_GET(self):
        rows, pages, done = load_state()
        url = urllib.parse.urlparse(self.path)
        qs = urllib.parse.parse_qs(url.query)
        filt = qs.get('f', ['all'])[0]

        if url.path == '/':
            return self.index(rows, pages, done, filt)
        if url.path.startswith('/item/'):
            return self.item(rows, pages, done, int(url.path[6:]), filt)
        if url.path.startswith('/page/'):
            _, _, stem, pg = url.path.split('/')
            png = page_png(stem, int(pg))
            if not png:
                return self.send_html('<p>PDF not synced yet.</p>', 404)
            data = png.read_bytes()
            self.send_response(200)
            self.send_header('Content-Type', 'image/png')
            self.send_header('Content-Length', str(len(data)))
            self.end_headers()
            self.wfile.write(data)
            return
        self.send_html('<p>not found</p>', 404)

    def filtered(self, rows, filt):
        if filt == 'wood':
            return [(i, r) for i, r in enumerate(rows) if is_wood(r)]
        if filt == 'canada':
            return [(i, r) for i, r in enumerate(rows)
                    if 'north america' in (r['country'] or '').lower()
                    or 'canada' in (r['country'] or '').lower()]
        return list(enumerate(rows))

    def index(self, rows, pages, done, filt):
        sel = self.filtered(rows, filt)
        n_done = sum(1 for _, r in sel if row_key(r) in done)
        body = [f'<div style="padding:18px;max-width:1100px">'
                f'<h2>Review queue — {len(sel):,} rows, {n_done:,} done</h2>'
                f'<p class="filter">Filter: '
                f'<a href="/?f=all">all</a> <a href="/?f=wood">wood</a> '
                f'<a href="/?f=canada">canada</a> (current: {filt})</p>'
                '<table><tr><th></th><th>vol</th><th>flow</th><th>group</th>'
                '<th>article</th><th>country</th><th>yr</th>'
                '<th>qty</th><th>value £</th><th>page</th><th></th></tr>']
        for i, r in sel[:400]:
            k = row_key(r)
            pg = pages.get(k)
            st = ('<span class="done">✓ ' + esc(done[k]['decision'])
                  + '</span>') if k in done else ''
            body.append(
                f'<tr><td>{st}</td><td>{esc(r["volume"])}</td>'
                f'<td>{esc(r["flow"])}</td><td>{esc(r["group"])[:26]}</td>'
                f'<td>{esc(r["article"])[:26]}</td>'
                f'<td>{esc(r["country"])[:24]}</td><td>{esc(r["year"])}</td>'
                f'<td align=right>{esc(r["quantity"])}</td>'
                f'<td align=right>{esc(r["value"])}</td>'
                f'<td>{pg["page"] if pg else "?"}</td>'
                f'<td><a href="/item/{i}?f={filt}">open</a></td></tr>')
        body.append('</table><p>(first 400 shown, ranked by £ exposure)'
                    '</p></div>')
        self.send_html(''.join(body))

    def item(self, rows, pages, done, i, filt):
        r = rows[i]
        k = row_key(r)
        pg = pages.get(k)
        sel = self.filtered(rows, filt)
        nxt = next((j for j, rr in sel if j > i
                    and row_key(rr) not in done), None)
        d = done.get(k)
        img = (f'<img src="/page/{pg["pdf"]}/{pg["page"]}">' if pg
               else '<p style="color:#fff;padding:40px">page not located '
                    '— use the OCR context below</p>')
        decided = (f'<p class="done">already decided: {esc(d["decision"])} '
                   f'q={esc(d["quantity"])} v={esc(d["value"])}</p>'
                   if d else '')
        body = f"""
<div id="side">
 <p><a href="/?f={filt}">← queue</a>
 {f'&nbsp; <a href="/item/{nxt}?f={filt}">next unreviewed →</a>' if nxt is not None else ''}</p>
 <table>
  <tr><td class=k>volume</td><td class=v>{esc(r['volume'])}</td></tr>
  <tr><td class=k>flow / duty</td><td>{esc(r['flow'])} {esc(r['duty'])}</td></tr>
  <tr><td class=k>group</td><td class=v>{esc(r['group'])}</td></tr>
  <tr><td class=k>article</td><td class=v>{esc(r['article'])}</td></tr>
  <tr><td class=k>country</td><td class=v>{esc(r['country'])}</td></tr>
  <tr><td class=k>year</td><td>{esc(r['year'])}</td></tr>
  <tr><td class=k>parsed quantity</td><td class=v>{esc(r['quantity'])}</td></tr>
  <tr><td class=k>parsed value £</td><td class=v>{esc(r['value'])}</td></tr>
  <tr><td class=k>block status</td><td>{esc(r['q_block'])} / {esc(r['v_block'])}
   <span class=badge>q/v</span></td></tr>
  <tr><td class=k>cell status</td><td>{esc(r['q_cell'])} / {esc(r['v_cell'])}</td></tr>
  <tr><td class=k>page</td><td>{pg['page'] if pg else '?'} of {esc(pg['pdf']) if pg else ''}</td></tr>
 </table>
 {decided}
 <form method=post action="/decide">
  <input type=hidden name=key value="{esc(k)}">
  <input type=hidden name=next value="{nxt if nxt is not None else ''}">
  <input type=hidden name=f value="{esc(filt)}">
  <p>quantity <input type=text name=quantity value="{esc(r['quantity'])}">
     value £ <input type=text name=value value="{esc(r['value'])}"></p>
  <button name=decision value=confirm class=confirm>✓ printed page matches
   these numbers</button><br>
  <button name=decision value=correct>save corrected numbers</button><br>
  <button name=decision value=notfound class=nf>can't find on page</button>
  <button name=decision value=junk class=junk>junk row (not real data)</button>
 </form>
</div>
<div id="main">{img}</div>"""
        self.send_html(body)

    def do_POST(self):
        ln = int(self.headers.get('Content-Length', 0))
        form = urllib.parse.parse_qs(self.rfile.read(ln).decode())
        get = lambda f: form.get(f, [''])[0]
        new = not DECISIONS.exists()
        with open(DECISIONS, 'a', newline='') as fh:
            w = csv.writer(fh)
            if new:
                w.writerow(['key', 'decision', 'quantity', 'value', 'ts'])
            w.writerow([get('key'), get('decision'), get('quantity'),
                        get('value'), datetime.now().isoformat(' ',
                                                               'seconds')])
        nxt, filt = get('next'), get('f') or 'all'
        dest = f'/item/{nxt}?f={filt}' if nxt else f'/?f={filt}'
        self.send_response(303)
        self.send_header('Location', dest)
        self.end_headers()


if __name__ == '__main__':
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8077
    print(f'review app -> http://localhost:{port}')
    HTTPServer(('127.0.0.1', port), H).serve_forever()

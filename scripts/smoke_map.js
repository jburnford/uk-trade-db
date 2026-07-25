/* Headless smoke test for exports/trade_origins_map.html.
 *
 * The artifact is 2MB of generated HTML with no build step and no tests, so a
 * template edit that breaks the picker or the draw loop is invisible until
 * somebody opens the page. This runs it in jsdom and exercises the paths a
 * reader actually takes. It caught two real faults on its first run: focusing
 * the search box listed only matches for the name already in it, and the
 * automatic fall back to Quantity for a value-less commodity stuck for every
 * commodity chosen afterwards.
 *
 * jsdom is the only dependency and this repo has no package.json, so install
 * it wherever is convenient and point NODE_PATH at that node_modules:
 *
 *   npm install --prefix ~/.local/js jsdom
 *   NODE_PATH=~/.local/js/node_modules node scripts/smoke_map.js
 *
 * An artifact path may be passed as the first argument (default:
 * exports/trade_origins_map.html).
 *
 * Exits non-zero on any failed assertion or page error.
 */
const fs = require('fs');
const path = require('path');
let JSDOM;
try {
  ({ JSDOM } = require('jsdom'));
} catch (e) {
  console.error('smoke_map: jsdom not found. Install it and set NODE_PATH:\n'
    + '  npm install --prefix ~/.local/js jsdom\n'
    + '  NODE_PATH=~/.local/js/node_modules node scripts/smoke_map.js');
  process.exit(2);
}

const file = process.argv[2] || path.join(__dirname, '..', 'exports',
                                          'trade_origins_map.html');
const html = fs.readFileSync(file, 'utf8');
const errs = [];
const fails = [];
const ok = (cond, msg) => { console.log(`${cond ? ' ok ' : 'FAIL'}  ${msg}`);
                            if (!cond) fails.push(msg); };

const dom = new JSDOM(`<!doctype html><html><head></head><body>${html}</body></html>`,
                      { runScripts: 'dangerously', pretendToBeVisual: true });
dom.virtualConsole.on('jsdomError', e => errs.push(e.message));
const w = dom.window, d = w.document;

setTimeout(() => {
  const $ = s => d.querySelector(s);
  const D = JSON.parse($('#dataset').textContent);
  const C = D.commodities, names = Object.keys(C);
  const withFlag = f => names.find(n => (C[n].q || []).includes(f));
  const clean = names.find(n => !(C[n].q || []).length);

  ok(names.length > 500, `dataset loaded (${names.length} commodities)`);
  ok(!!D.meta.flag_note, 'quality flag glossary is present');
  ok((D.land || []).length > 20, `land outlines present (${(D.land||[]).length} rings)`);

  // picker opens on the full list, not filtered by whatever name is in the box
  $('#search').dispatchEvent(new w.Event('focus'));
  const items = d.querySelectorAll('.pickitem').length;
  ok(items > 50, `focus opens the browse list (${items} items)`);
  ok(d.querySelectorAll('.cattab').length > 5, 'category tabs render');

  // the well-measured filter actually filters
  const cb = d.querySelector('.cattab[data-clean]');
  ok(!!cb, 'well-measured-only filter exists');
  cb.dispatchEvent(new w.MouseEvent('mousedown', { bubbles: true }));
  ok(d.querySelectorAll('.pickitem.flagged').length === 0,
     'filter hides every flagged commodity');
  cb.dispatchEvent(new w.MouseEvent('mousedown', { bubbles: true }));

  // caveats show, and the value toggle is honest about having no values
  w.eval(`select(${JSON.stringify(withFlag('noval'))})`);
  ok($('#qnote').classList.contains('show'), 'flagged commodity shows its caveats');
  ok(d.querySelector('#measure button[data-m="v"]').disabled,
     'value toggle disabled when there are no value figures');
  ok(w.eval('state.meas') === 'q', 'measure falls back to quantity');
  w.eval(`select(${JSON.stringify(clean)})`);
  ok(!$('#qnote').classList.contains('show'), 'clean commodity shows no caveats');
  ok(w.eval('state.meas') === 'v', "reader's measure is restored, not left on the fallback");
  ok(d.querySelectorAll('#map circle').length > 0, 'clean commodity draws bubbles');
  const lp = d.querySelector('#map path');
  ok(!!lp && lp.getAttribute('d').length > 5000, 'coastlines drawn under the bubbles');

  // a commodity with nothing mappable must not throw on the way to a blank map
  const no = withFlag('noorig');
  if (no) {
    w.eval(`select(${JSON.stringify(no)})`);
    ok(d.querySelectorAll('#map circle').length === 0,
       'unmappable commodity draws no bubbles and does not throw');
  }

  // year control
  const y = $('#year');
  y.value = y.max;
  y.dispatchEvent(new w.Event('input'));
  ok($('#yearlbl').textContent === y.max, 'year slider updates the label');

  ok(errs.length === 0, `no page errors${errs.length ? ': ' + errs.join(' | ') : ''}`);
  console.log(fails.length ? `\n${fails.length} FAILED` : '\nall checks passed');
  process.exit(fails.length ? 1 : 0);
}, 800);

// Smoke test for reports/canada_imports_from_uk.html
// Runs the page under jsdom and checks the rendered SVG geometry. This cannot
// see visual layout, but it catches the failures that actually ship: a JS
// error that leaves the chart blank, NaN coordinates, a line joined across a
// year that has no data, and a table that disagrees with the plotted series.
//   NODE_PATH=~/.local/js/node_modules node scripts/smoke_canada_chart.js
const fs = require('fs');
const { JSDOM } = require('jsdom');

const html = fs.readFileSync('reports/canada_imports_from_uk.html', 'utf8');
let fails = 0, passes = 0;
const errs = [];

function check(name, cond, detail) {
  if (cond) { passes++; console.log(`  PASS  ${name}`); }
  else { fails++; console.log(`  FAIL  ${name}${detail ? '  — ' + detail : ''}`); }
}

const dom = new JSDOM(html, { runScripts: 'dangerously', pretendToBeVisual: true });
dom.virtualConsole.on('jsdomError', e => errs.push(e.message));
const doc = dom.window.document;

console.log('rendering under jsdom…\n');
check('no JS errors during render', errs.length === 0, errs.join(' | '));

const s1 = doc.getElementById('s1'), s2 = doc.getElementById('s2');
check('chart 1 rendered content', s1 && s1.childNodes.length > 0);
check('chart 2 rendered content', s2 && s2.childNodes.length > 0);

// no NaN / undefined anywhere in the emitted SVG attributes
for (const [id, svg] of [['s1', s1], ['s2', s2]]) {
  let bad = 0;
  svg.querySelectorAll('*').forEach(n => {
    for (const a of n.attributes || []) {
      if (/NaN|undefined|Infinity/.test(a.value)) bad++;
    }
  });
  check(`${id}: no NaN/undefined coordinates`, bad === 0, `${bad} bad attributes`);
}

// 1871 has no volume: the Canada line must be BROKEN, not interpolated
const p1 = [...s1.querySelectorAll('path')].filter(p => p.getAttribute('stroke') === 'var(--series-1)');
check('chart 1: Canada line split into 2 segments at the 1871 gap',
  p1.length === 2, `found ${p1.length}`);

// corroboration strip: one cell per year that has data (31 years - 1871 = 30)
const cells = [...s1.querySelectorAll('rect')].filter(r => /var\(--c[1-4]\)/.test(r.getAttribute('fill') || ''));
check('chart 1: corroboration strip has 30 cells', cells.length === 30, `found ${cells.length}`);

// strip cells must sit BELOW the plot area, never over the line
const minStripY = Math.min(...cells.map(c => +c.getAttribute('y')));
const lineYs = (p1[0].getAttribute('d').match(/[\d.]+(?=\s|$)/g) || []).map(Number);
check('chart 1: strip sits below the plotted line', minStripY > Math.min(...lineYs));

// chart 2: five series, exactly one of them the emphasis colour
const emph = [...s2.querySelectorAll('path')].filter(p => p.getAttribute('stroke') === 'var(--series-1)');
const ctx = [...s2.querySelectorAll('path')].filter(p => p.getAttribute('stroke') === 'var(--context)');
check('chart 2: Canada drawn in the emphasis hue', emph.length >= 1);
check('chart 2: four context series in gray', ctx.length >= 4, `found ${ctx.length}`);
check('chart 2: emphasis line is heavier than context',
  +emph[0].getAttribute('stroke-width') > +ctx[0].getAttribute('stroke-width'));

// every series is direct-labelled, so identity never rests on colour alone
const labels = [...s2.querySelectorAll('text')].map(t => t.textContent);
['Canada', 'Australasia', 'Germany', 'France', 'Netherlands'].forEach(n =>
  check(`chart 2: "${n}" direct-labelled`, labels.includes(n)));

// accessibility: alt text, table view, and the table must match the series
check('both charts carry an aria-label',
  (s1.getAttribute('aria-label') || '').length > 30 &&
  (s2.getAttribute('aria-label') || '').length > 30);

doc.getElementById('tgl').dispatchEvent(new dom.window.Event('click'));
const rows = doc.querySelectorAll('#tbl tbody tr');
check('table view renders 31 rows (1870–1900)', rows.length === 31, `found ${rows.length}`);
const r1871 = [...rows].find(r => r.cells[0].textContent === '1871');
check('table marks 1871 as missing, not zero', r1871 && r1871.cells[1].textContent === '—');
const r1881 = [...rows].find(r => r.cells[0].textContent === '1881');
check('table 1881 matches the panel value (12,205,572)',
  r1881 && r1881.cells[1].textContent === '12,205,572', r1881 && r1881.cells[1].textContent);

// dark mode must be declared, not left to an automatic flip
check('dark mode declared for both OS setting and theme toggle',
  /prefers-color-scheme: dark/.test(html) && /\[data-theme="dark"\]/.test(html));
check('no dual-axis (single y scale per chart)', !/y2Scale|secondAxis/.test(html));

console.log(`\n${passes} passed, ${fails} failed`);
process.exit(fails ? 1 : 0);

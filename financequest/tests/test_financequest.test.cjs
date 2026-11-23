
const { test } = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');

// Load the existing FinanceQuest JavaScript source.
const source = fs.readFileSync(
  path.join(__dirname, '../static/js/app.js'),
  'utf8'
);

// Extract the actual functions without modifying app.js.
function extract(start, end) {
  const from = source.indexOf(start);
  assert.notEqual(from, -1, `Missing: ${start}`);

  const to = source.indexOf(end, from + start.length);
  assert.notEqual(to, -1, `Missing: ${end}`);

  return source.slice(from, to);
}

const pctCode = extract('pct=', ',save=');
const growthCode = extract('avgGrowth=', ',plant=');
const escapeCode = extract('function escapeHTML(str)', 'function txHTML');

// Run the existing functions in an isolated context.
function run(code, expression, state = {}) {
  return vm.runInNewContext(
    `const ${code}; ${expression}`,
    { state },
    { timeout: 1000 }
  );
}

// 1. Savings percentage tests
test('pct: normal savings progress', () => {
  assert.equal(run(pctCode, 'pct(50, 100)'), 50);
});

test('pct: completed savings goal', () => {
  assert.equal(run(pctCode, 'pct(100, 100)'), 100);
});

test('pct: savings exceed target', () => {
  assert.equal(run(pctCode, 'pct(150, 100)'), 100);
});

test('pct: zero target should be handled', () => {
  assert.equal(run(pctCode, 'pct(0, 0)'), 0);
});

test('pct: negative savings should not show negative progress', () => {
  assert.equal(run(pctCode, 'pct(-20, 100)'), 0);
});

// 2. Mascot growth tests
function mascotStage(saved, target = 100) {
  const state = {
    goals: [{ id: 1, saved, target }]
  };
  return run(growthCode, 'stage()', state);
}

test('mascot: initial stage', () => {
  assert.equal(mascotStage(0), 1);
});

test('mascot: stage 2 at 25 percent', () => {
  assert.equal(mascotStage(25), 2);
});

test('mascot: stage 3 at 55 percent', () => {
  assert.equal(mascotStage(55), 3);
});

test('mascot: stage 4 at 90 percent', () => {
  assert.equal(mascotStage(90), 4);
});

// 3. HTML input handling tests
function escape(value) {
  return vm.runInNewContext(
    `${escapeCode}; escapeHTML(value)`,
    { value },
    { timeout: 1000 }
  );
}

test('HTML: normal text', () => {
  assert.equal(escape('FinanceQuest'), 'FinanceQuest');
});

test('HTML: special characters', () => {
  assert.equal(escape('<test>'), '&lt;test&gt;');
});

test('HTML: potentially unsafe markup', () => {
  assert.equal(
    escape('<script>alert(1)</script>'),
    '&lt;script&gt;alert(1)&lt;/script&gt;'
  );
});

test('HTML: empty input', () => {
  assert.equal(escape(''), '');
});


 // Additional boundary and error-handling tests

// TC-14: Invalid savings input
test('pct: nonnumeric savings input', () => {
  assert.equal(run(pctCode, 'pct("abc", 100)'), 0);
});

// TC-15: Mascot with no savings goals
test('mascot: no savings goals', () => {
  assert.equal(run(growthCode, 'stage()', { goals: [] }), 1);
});

// TC-16: Mascot with invalid zero target
test('mascot: positive savings with zero target', () => {
  assert.equal(mascotStage(100, 0), 1);
});

// TC-17: Mascot with negative savings
test('mascot: negative savings progress', () => {
  assert.equal(mascotStage(-20), 1);
});

// TC-18: HTML escaping of multiple special characters
test('HTML: quotes and ampersands', () => {
  assert.equal(
    escape('Tom & "Jerry"'),
    'Tom &amp; &quot;Jerry&quot;'
  );
});


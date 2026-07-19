/*
 * Math Bastion: The History of Ideas
 * A tower-defense game where mathematical ideas are the technology tree.
 * All art is drawn procedurally on canvas; audio is synthesized with WebAudio.
 * (c) Eric Kvale — released with the site source. No third-party assets.
 */
(function () {
  'use strict';

  var root = document.getElementById('mb-game');
  if (!root) return;

  var URLS = {
    leaderboard: root.dataset.leaderboardUrl,
    submit: root.dataset.scoreUrl,
    csrf: root.dataset.csrf,
  };

  // ------------------------------------------------------------------
  // Constants
  // ------------------------------------------------------------------
  var COLS = 16, ROWS = 9, CELL = 60;
  var W = COLS * CELL, H = ROWS * CELL;
  var LIVES_START = 20, GOLD_START = 220;
  var SELL_RATIO = 0.7;

  // ------------------------------------------------------------------
  // Eras: history drives the campaign. Each era = new map, new mentor,
  // new discoveries (towers) and six waves ending in a boss.
  // ------------------------------------------------------------------
  var ERAS = [
    {
      id: 'prehistory',
      name: 'Prehistoric Counting',
      years: 'c. 20,000 BCE',
      palette: { bg: '#2e2a26', bg2: '#3a332c', path: '#6b5b45', pathEdge: '#4f4335', deco: '#514639' },
      mentor: {
        name: 'Onna, Keeper of the Tally Bone',
        emoji: '🦴',
        lines: [
          'The herds come at night, and no one remembers how many we drove off before.',
          'So I cut a notch in this bone for each one. One notch, one beast. Count them — counting is how we stop being surprised.',
        ],
        discovery: 'Counting & Tally Marks',
        blurb: 'The Ishango bone (c. 20,000 BCE) carries some of the oldest known tally marks. Before numerals existed, humans matched one mark to one thing — the root idea of all arithmetic.',
      },
      unlocks: ['tally', 'add'],
      path: [[-1, 4], [3, 4], [3, 1], [8, 1], [8, 7], [12, 7], [12, 3], [16, 3]],
      waves: [
        [{ t: 'imp', n: 6, gap: 1.1 }],
        [{ t: 'imp', n: 9, gap: 0.9 }],
        [{ t: 'imp', n: 6, gap: 0.9 }, { t: 'jackal', n: 4, gap: 0.7 }],
        [{ t: 'jackal', n: 8, gap: 0.55 }],
        [{ t: 'imp', n: 10, gap: 0.7 }, { t: 'jackal', n: 5, gap: 0.55 }],
        [{ t: 'imp', n: 6, gap: 0.8 }, { t: 'boss_mammoth', n: 1, gap: 1 }],
      ],
    },
    {
      id: 'egypt',
      name: 'Mesopotamia & Egypt',
      years: 'c. 3,000 BCE',
      palette: { bg: '#c9a76a', bg2: '#d4b57e', path: '#8a6a3d', pathEdge: '#6e5330', deco: '#b08d52' },
      mentor: {
        name: 'Ahmes, Scribe of the Rhind Papyrus',
        emoji: '📜',
        lines: [
          'The Nile flood erases every field boundary, every year. The tax collector still comes.',
          'We survey with ropes and split grain into parts — halves, thirds, fourths. Whoever masters fractions, masters the harvest.',
        ],
        discovery: 'Fractions & Multiplication',
        blurb: 'Egyptian scribes like Ahmes (c. 1550 BCE) computed with unit fractions to divide bread and land; Babylonians built multiplication tables in base 60 — we still use their 60s in minutes and degrees.',
      },
      unlocks: ['mult', 'frac'],
      path: [[-1, 1], [5, 1], [5, 5], [2, 5], [2, 7], [10, 7], [10, 2], [13, 2], [13, 5], [16, 5]],
      waves: [
        [{ t: 'imp', n: 8, gap: 0.8 }, { t: 'slime', n: 3, gap: 1.2 }],
        [{ t: 'slime', n: 6, gap: 1.0 }],
        [{ t: 'jackal', n: 8, gap: 0.5 }, { t: 'slime', n: 4, gap: 1.0 }],
        [{ t: 'imp', n: 12, gap: 0.55 }, { t: 'jackal', n: 6, gap: 0.5 }],
        [{ t: 'slime', n: 8, gap: 0.8 }, { t: 'jackal', n: 6, gap: 0.45 }],
        [{ t: 'slime', n: 4, gap: 0.9 }, { t: 'boss_sphinx', n: 1, gap: 1 }],
      ],
    },
    {
      id: 'greece',
      name: 'Ancient Greece',
      years: 'c. 500 BCE',
      palette: { bg: '#e8e2d4', bg2: '#efe9dc', path: '#b9ad94', pathEdge: '#9a8f79', deco: '#cfc6b2' },
      mentor: {
        name: 'Euclid of Alexandria',
        emoji: '📐',
        lines: [
          'Anyone can see that a fact is true. The Greeks asked a harder question: can you prove it must be?',
          'Give me a straightedge and compass. From five simple postulates we will build defenses no chaos can argue with.',
        ],
        discovery: 'Geometry, Proof & Primes',
        blurb: 'Euclid\u2019s Elements (c. 300 BCE) organized geometry into proofs from axioms and showed there are infinitely many primes — numbers divisible only by 1 and themselves, the atoms of arithmetic.',
      },
      unlocks: ['prime', 'geo'],
      path: [[-1, 7], [4, 7], [4, 3], [8, 3], [8, 6], [12, 6], [12, 1], [16, 1]],
      waves: [
        [{ t: 'primegob', n: 5, gap: 1.0 }, { t: 'imp', n: 6, gap: 0.6 }],
        [{ t: 'golem', n: 4, gap: 1.4 }],
        [{ t: 'primegob', n: 7, gap: 0.8 }, { t: 'jackal', n: 8, gap: 0.4 }],
        [{ t: 'golem', n: 5, gap: 1.2 }, { t: 'slime', n: 6, gap: 0.8 }],
        [{ t: 'primegob', n: 8, gap: 0.7 }, { t: 'golem', n: 4, gap: 1.2 }],
        [{ t: 'golem', n: 3, gap: 1.2 }, { t: 'boss_drake', n: 1, gap: 1 }],
      ],
    },
    {
      id: 'goldenage',
      name: 'India & the Islamic Golden Age',
      years: 'c. 800 CE',
      palette: { bg: '#1f2c4d', bg2: '#25335a', path: '#7a6a9c', pathEdge: '#5d4f7c', deco: '#33406b' },
      mentor: {
        name: 'Al-Khwarizmi of the House of Wisdom',
        emoji: '⭐',
        lines: [
          'In Baghdad we gathered every book we could find — Greek, Indian, Persian — and read them all.',
          'From India came a gift: a symbol for nothing. Zero. With it, and with al-jabr — restoring balance to equations — the unknown itself becomes a thing you can hunt.',
        ],
        discovery: 'Zero & Algebra',
        blurb: 'Brahmagupta (628 CE) gave rules for zero and negatives; Al-Khwarizmi\u2019s book on al-jabr (c. 820 CE) named algebra, and Latin translations of his name gave us the word "algorithm."',
      },
      unlocks: ['zero', 'alg'],
      path: [[-1, 2], [3, 2], [3, 6], [7, 6], [7, 1], [11, 1], [11, 7], [14, 7], [14, 4], [16, 4]],
      waves: [
        [{ t: 'negspirit', n: 6, gap: 0.8 }, { t: 'imp', n: 8, gap: 0.5 }],
        [{ t: 'negspirit', n: 8, gap: 0.6 }, { t: 'primegob', n: 5, gap: 0.9 }],
        [{ t: 'golem', n: 6, gap: 1.0 }, { t: 'negspirit', n: 6, gap: 0.6 }],
        [{ t: 'slime', n: 8, gap: 0.7 }, { t: 'jackal', n: 10, gap: 0.35 }],
        [{ t: 'negspirit', n: 10, gap: 0.5 }, { t: 'golem', n: 5, gap: 1.0 }],
        [{ t: 'negspirit', n: 6, gap: 0.6 }, { t: 'boss_djinn', n: 1, gap: 1 }],
      ],
    },
    {
      id: 'revolution',
      name: 'The Scientific Revolution',
      years: 'c. 1600–1700 CE',
      palette: { bg: '#efe6cf', bg2: '#f4ecd8', path: '#a89468', pathEdge: '#8a7852', deco: '#d9cdae' },
      mentor: {
        name: 'Isaac Newton',
        emoji: '🍎',
        lines: [
          'Descartes taught us to give every point an address — two numbers, and geometry becomes algebra.',
          'I needed more: the mathematics of change itself. Call it the calculus. If I have seen further, it is by standing on the shoulders of giants. Now — hold the line.',
        ],
        discovery: 'Coordinates, Probability & Calculus',
        blurb: 'Descartes\u2019 coordinates (1637) fused algebra with geometry; Pascal and Fermat founded probability (1654); Newton and Leibniz independently invented calculus — the mathematics of motion and change.',
      },
      unlocks: ['coord', 'deriv', 'prob'],
      path: [[-1, 5], [2, 5], [2, 2], [6, 2], [6, 7], [10, 7], [10, 2], [14, 2], [14, 6], [16, 6]],
      waves: [
        [{ t: 'chaos', n: 6, gap: 0.9 }, { t: 'jackal', n: 8, gap: 0.4 }],
        [{ t: 'chaos', n: 8, gap: 0.7 }, { t: 'golem', n: 5, gap: 1.0 }],
        [{ t: 'primegob', n: 10, gap: 0.5 }, { t: 'negspirit', n: 8, gap: 0.5 }],
        [{ t: 'chaos', n: 10, gap: 0.6 }, { t: 'slime', n: 8, gap: 0.6 }],
        [{ t: 'golem', n: 8, gap: 0.8 }, { t: 'chaos', n: 8, gap: 0.55 }, { t: 'jackal', n: 10, gap: 0.3 }],
        [{ t: 'chaos', n: 5, gap: 0.8 }, { t: 'boss_hydra', n: 1, gap: 1 }],
      ],
    },
  ];

  // ------------------------------------------------------------------
  // Towers — every tower is a mathematical idea used as a tool.
  // ------------------------------------------------------------------
  var TOWERS = {
    tally: {
      name: 'Tally Slinger', sym: '𝍫', cost: 50, range: 130, period: 0.8, dmg: 8,
      color: '#a67c52', proj: '#e8d5b5',
      desc: 'One stone per beast. Simple, honest, one-to-one counting.',
      hist: 'One notch, one thing: tally sticks are humanity\u2019s oldest data structure.',
    },
    add: {
      name: 'Addition Tower', sym: '+', cost: 80, range: 120, period: 0.5, dmg: 4,
      color: '#c98d3f', proj: '#ffe1a1',
      desc: 'Damage adds up: each consecutive hit on the same target hits +2 harder (stacks to 20).',
      hist: 'Sumerian accountants invented addition to track grain and livestock debts.',
    },
    mult: {
      name: 'Multiplication Cannon', sym: '×', cost: 120, range: 140, period: 1.6, dmg: 14,
      color: '#b3552e', proj: '#ff9d66', splash: 60,
      desc: 'Why add when you can multiply? Shells explode, damaging everything nearby.',
      hist: 'Babylonian scribes pressed multiplication tables into clay 4,000 years ago.',
    },
    frac: {
      name: 'Fraction Splitter', sym: '½', cost: 90, range: 130, period: 1.2, dmg: 6,
      color: '#3f7fbf', proj: '#a8d1ff', slow: 0.5, slowDur: 2,
      desc: 'Cuts an enemy\u2019s speed in half for 2s. Half of a half is a quarter\u2026',
      hist: 'Egyptian scribes wrote every fraction as a sum of unit fractions: 1/2, 1/3, 1/4…',
    },
    prime: {
      name: 'Prime Watchtower', sym: 'ℙ', cost: 110, range: 150, period: 1.0, dmg: 10,
      color: '#7b4fa6', proj: '#d3b3ff', primeMult: 4,
      desc: 'Tuned to the atoms of arithmetic: ×4 damage to PRIME enemies, and ignores prime armor.',
      hist: 'Euclid proved there are infinitely many primes around 300 BCE.',
    },
    geo: {
      name: 'Geometry Beacon', sym: '△', cost: 150, range: 160, period: 2.0, dmg: 13,
      color: '#2e8b74', proj: '#9fe8d8', beam: true,
      desc: 'Fires a straightedge ray that pierces every enemy along the line.',
      hist: 'A straight line can be drawn between any two points — Euclid, Postulate 1.',
    },
    zero: {
      name: 'Zero Well', sym: '0', cost: 100, range: 110, period: 0, dmg: 0,
      color: '#274b8f', proj: '#fff', aura: 'slow', auraSlow: 0.65,
      desc: 'A well of nothing. Enemies in its aura slow toward zero (-35% speed).',
      hist: 'Brahmagupta treated zero as a number with rules of its own in 628 CE.',
    },
    alg: {
      name: 'Algebra Obelisk', sym: '𝑥', cost: 140, range: 140, period: 1.4, dmg: 8,
      color: '#8f6a27', proj: '#ffe97a', hpPct: 0.07,
      desc: 'Solves for the unknown: bonus damage equal to 7% of the target\u2019s current HP.',
      hist: 'Al-jabr means "restoring balance" — moving terms across the equals sign.',
    },
    coord: {
      name: 'Coordinate Sniper', sym: '⌖', cost: 170, range: 9999, period: 2.2, dmg: 45,
      color: '#3a3f8f', proj: '#c3c7ff', targeting: 'strong',
      desc: 'Every point on the map has an (x, y) address. Unlimited range; targets the strongest enemy.',
      hist: 'Descartes unified algebra and geometry with coordinates in 1637.',
    },
    deriv: {
      name: 'Derivative Accelerator', sym: 'd/dx', cost: 130, range: 100, period: 0, dmg: 0,
      color: '#a3402e', proj: '#fff', aura: 'haste', auraHaste: 0.30,
      desc: 'The mathematics of rate-of-change: nearby towers fire 30% faster.',
      hist: 'The derivative measures how fast things change — Newton & Leibniz, 1660s–70s.',
    },
    prob: {
      name: 'Probability Mage', sym: '🎲', cost: 160, range: 140, period: 0.9, dmg: 9,
      color: '#356e35', proj: '#b1e6a3', crit: 0.25, critMult: 5,
      desc: 'Expected value is excellent: 25% chance of a ×5 critical hit.',
      hist: 'Pascal and Fermat invented probability theory arguing over a dice game in 1654.',
    },
  };

  // Per-level upgrade scaling (levels 1..3; index 0 is base).
  var UPG = { dmg: 1.5, period: 0.88, range: 1.1, costRatio: 0.8 };

  // ------------------------------------------------------------------
  // Enemies — obstacles that force different mathematical tools.
  // ------------------------------------------------------------------
  var ENEMIES = {
    imp: { name: 'Count Imp', hp: 30, spd: 62, gold: 6, r: 12, color: '#c05b4d', nums: [1, 4, 6, 8, 9] },
    jackal: { name: 'Swift Jackal', hp: 20, spd: 112, gold: 6, r: 10, color: '#d99a3d', nums: [1, 2, 3] },
    slime: {
      name: 'Fraction Slime', hp: 48, spd: 46, gold: 5, r: 14, color: '#4da3c0', label: '1/1',
      splitsInto: 'half',
    },
    half: { name: 'Half Slime', hp: 24, spd: 56, gold: 3, r: 10, color: '#5fb3cf', label: '1/2', splitsInto: 'quarter', noWaveCount: true },
    quarter: { name: 'Quarter Slime', hp: 12, spd: 66, gold: 2, r: 7, color: '#79c4dc', label: '1/4', noWaveCount: true },
    primegob: {
      name: 'Prime Goblin', hp: 55, spd: 66, gold: 10, r: 12, color: '#8d5fc0',
      prime: true, armor: 0.55, nums: [2, 3, 5, 7, 11, 13],
    },
    golem: {
      name: 'Composite Golem', hp: 130, spd: 36, gold: 14, r: 16, color: '#7d7d6e',
      composite: true, factorSets: [[2, 2, 3], [2, 3, 3], [2, 2, 5], [2, 2, 2, 3]],
    },
    factorling: { name: 'Factorling', hp: 18, spd: 80, gold: 2, r: 8, color: '#9a9a88', prime: true, noWaveCount: true },
    negspirit: {
      name: 'Negative Spirit', hp: 35, spd: 96, gold: 8, r: 11, color: '#5a6b9e',
      ghost: true, leakSteal: 15, nums: [-1, -2, -3, -5],
    },
    chaos: {
      name: 'Chaos Equation', hp: 75, spd: 62, gold: 12, r: 13, color: '#b04a8f',
      chaotic: true, label: '?!',
    },
    boss_mammoth: {
      name: 'Mammoth of Ignorance', hp: 550, spd: 26, gold: 90, r: 26, color: '#8a6f5a',
      boss: true, label: '?',
    },
    boss_sphinx: {
      name: 'Sphinx of Riddles', hp: 850, spd: 30, gold: 110, r: 26, color: '#c2a24e',
      boss: true, label: '?', splitJackals: 6,
    },
    boss_drake: {
      name: 'Polynomial Drake', hp: 1300, spd: 32, gold: 140, r: 27, color: '#3e7d5a',
      boss: true, label: 'xⁿ', spawnEvery: 5, spawnType: 'jackal',
    },
    boss_djinn: {
      name: 'Chaos Djinn', hp: 1800, spd: 40, gold: 170, r: 25, color: '#6a4ac2',
      boss: true, label: '≠', teleportEvery: 4, teleportDist: 70,
    },
    boss_hydra: {
      name: 'The Infinite Hydra', hp: 3200, spd: 26, gold: 300, r: 30, color: '#345e46',
      boss: true, label: '∞', hydra: true,
    },
  };

  // ------------------------------------------------------------------
  // Codex: what you actually discovered, unlocked as you play.
  // ------------------------------------------------------------------
  var CODEX = ERAS.map(function (e) {
    return { era: e.name, years: e.years, title: e.mentor.discovery, blurb: e.mentor.blurb, unlocked: false };
  });

  // ------------------------------------------------------------------
  // Audio: tiny synthesizer, no sound files.
  // ------------------------------------------------------------------
  var AudioSys = (function () {
    var ctx = null, muted = false;
    function ensure() {
      if (!ctx) {
        try { ctx = new (window.AudioContext || window.webkitAudioContext)(); } catch (e) { muted = true; }
      }
      if (ctx && ctx.state === 'suspended') ctx.resume();
    }
    function tone(freq, dur, type, vol, slide) {
      if (muted) return;
      ensure();
      if (!ctx) return;
      var o = ctx.createOscillator(), g = ctx.createGain();
      o.type = type || 'square';
      o.frequency.value = freq;
      if (slide) o.frequency.exponentialRampToValueAtTime(Math.max(30, freq + slide), ctx.currentTime + dur);
      g.gain.value = (vol || 0.04);
      g.gain.exponentialRampToValueAtTime(0.0001, ctx.currentTime + dur);
      o.connect(g); g.connect(ctx.destination);
      o.start(); o.stop(ctx.currentTime + dur);
    }
    return {
      shoot: function () { tone(620, 0.07, 'square', 0.025, -180); },
      boom: function () { tone(120, 0.25, 'sawtooth', 0.05, -60); },
      coin: function () { tone(880, 0.09, 'triangle', 0.05); tone(1320, 0.12, 'triangle', 0.04); },
      hurt: function () { tone(160, 0.3, 'sawtooth', 0.07, -80); },
      wave: function () { tone(440, 0.12, 'triangle', 0.05); tone(660, 0.18, 'triangle', 0.05); },
      fanfare: function () { [523, 659, 784, 1046].forEach(function (f, i) { setTimeout(function () { tone(f, 0.22, 'triangle', 0.06); }, i * 130); }); },
      place: function () { tone(330, 0.1, 'triangle', 0.05); },
      toggleMute: function () { muted = !muted; return muted; },
      isMuted: function () { return muted; },
    };
  })();

  // ------------------------------------------------------------------
  // Geometry helpers
  // ------------------------------------------------------------------
  function dist(ax, ay, bx, by) { var dx = ax - bx, dy = ay - by; return Math.sqrt(dx * dx + dy * dy); }

  function buildPath(cells) {
    var pts = cells.map(function (c) { return [c[0] * CELL + CELL / 2, c[1] * CELL + CELL / 2]; });
    var segs = [], total = 0;
    for (var i = 0; i < pts.length - 1; i++) {
      var len = dist(pts[i][0], pts[i][1], pts[i + 1][0], pts[i + 1][1]);
      segs.push({ a: pts[i], b: pts[i + 1], len: len, start: total });
      total += len;
    }
    return { pts: pts, segs: segs, total: total };
  }

  function pointAt(path, d) {
    if (d <= 0) { var s0 = path.segs[0]; return { x: s0.a[0], y: s0.a[1] }; }
    for (var i = 0; i < path.segs.length; i++) {
      var s = path.segs[i];
      if (d <= s.start + s.len) {
        var t = (d - s.start) / s.len;
        return { x: s.a[0] + (s.b[0] - s.a[0]) * t, y: s.a[1] + (s.b[1] - s.a[1]) * t };
      }
    }
    var last = path.segs[path.segs.length - 1];
    return { x: last.b[0], y: last.b[1] };
  }

  function blockedCells(cells) {
    var set = {};
    for (var i = 0; i < cells.length - 1; i++) {
      var x0 = cells[i][0], y0 = cells[i][1], x1 = cells[i + 1][0], y1 = cells[i + 1][1];
      var dx = Math.sign(x1 - x0), dy = Math.sign(y1 - y0);
      var x = x0, y = y0;
      set[x + ',' + y] = true;
      while (x !== x1 || y !== y1) {
        x += dx; y += dy;
        set[x + ',' + y] = true;
      }
    }
    return set;
  }

  // ------------------------------------------------------------------
  // Game state
  // ------------------------------------------------------------------
  var G = {
    state: 'menu',           // menu | dialog | build | wave | gameover | victory
    eraIdx: 0,
    waveIdx: 0,              // wave within era
    globalWave: 0,
    lives: LIVES_START,
    gold: GOLD_START,
    score: 0,
    speed: 1,
    paused: false,
    towers: [],
    enemies: [],
    projectiles: [],
    beams: [],
    floats: [],
    particles: [],
    spawnQueue: [],
    spawnTimer: 0,
    unlocked: {},
    selectedShop: null,
    selectedTower: null,
    hoverCell: null,
    path: null,
    blocked: {},
    time: 0,
    scoreSubmitted: false,
  };

  function era() { return ERAS[G.eraIdx]; }

  // ------------------------------------------------------------------
  // Enemy
  // ------------------------------------------------------------------
  var enemyId = 0;
  function makeEnemy(type, opts) {
    opts = opts || {};
    var def = ENEMIES[type];
    var scale = 1 + 0.11 * G.globalWave;
    var e = {
      id: ++enemyId,
      type: type,
      def: def,
      hp: def.hp * scale * (opts.hpMult || 1),
      maxHp: def.hp * scale * (opts.hpMult || 1),
      d: opts.d || 0,
      spd: def.spd,
      r: def.r,
      slows: [],
      dead: false,
      leaked: false,
      chaosTimer: 0,
      chaosBoost: 1,
      abilityTimer: 0,
      hydraStage: 0,
      label: def.label || null,
      num: null,
      prime: !!def.prime,
      wobble: Math.random() * Math.PI * 2,
    };
    if (def.nums) e.num = def.nums[Math.floor(Math.random() * def.nums.length)];
    if (def.composite && def.factorSets) {
      e.factors = def.factorSets[Math.floor(Math.random() * def.factorSets.length)];
      e.num = e.factors.reduce(function (a, b) { return a * b; }, 1);
    }
    return e;
  }

  function enemySpeed(e) {
    var mult = 1;
    for (var i = 0; i < e.slows.length; i++) mult = Math.min(mult, e.slows[i].mult);
    // Zero Well auras
    for (var j = 0; j < G.towers.length; j++) {
      var t = G.towers[j];
      if (t.def.aura === 'slow') {
        var p = pointAt(G.path, e.d);
        if (dist(t.x, t.y, p.x, p.y) <= t.range) mult = Math.min(mult, t.def.auraSlow - t.level * 0.08);
      }
    }
    return e.spd * Math.max(0.05, mult) * e.chaosBoost;
  }

  function damageEnemy(e, amount, opts) {
    opts = opts || {};
    var def = e.def;
    if (def.armor && !opts.ignoreArmor) amount *= def.armor;
    e.hp -= amount;
    if (opts.crit) addFloat(pointAt(G.path, e.d), 'CRIT ×' + opts.critMult + '!', '#ffd23f');
    if (e.hp <= 0 && !e.dead) killEnemy(e);
  }

  function killEnemy(e) {
    e.dead = true;
    var def = e.def;
    G.gold += def.gold;
    G.score += def.gold * 10;
    AudioSys.coin();
    var p = pointAt(G.path, e.d);
    addParticles(p.x, p.y, def.color, def.boss ? 26 : 8);
    addFloat(p, '+' + def.gold, '#f5d76e');

    // Fraction slimes split into halves, halves into quarters.
    if (def.splitsInto) {
      for (var i = 0; i < 2; i++) {
        G.enemies.push(makeEnemy(def.splitsInto, { d: Math.max(0, e.d - 6 + i * 12) }));
      }
    }
    // Composite golems decompose into their prime factors.
    if (e.factors) {
      for (var f = 0; f < e.factors.length; f++) {
        var child = makeEnemy('factorling', { d: Math.max(0, e.d - 10 + f * 10) });
        child.num = e.factors[f];
        G.enemies.push(child);
      }
    }
    // Sphinx releases a riddle of jackals.
    if (def.splitJackals) {
      for (var s = 0; s < def.splitJackals; s++) {
        G.enemies.push(makeEnemy('jackal', { d: Math.max(0, e.d - s * 14) }));
      }
    }
    if (def.boss) AudioSys.fanfare();
  }

  function updateEnemy(e, dt) {
    var def = e.def;
    e.wobble += dt * 6;
    e.slows = e.slows.filter(function (s) { return s.until > G.time; });

    if (def.chaotic) {
      e.chaosTimer -= dt;
      if (e.chaosTimer <= 0) {
        e.chaosBoost = (Math.random() < 0.4) ? 2.2 : 1;
        e.chaosTimer = 0.5 + Math.random() * 1.2;
      }
    }
    if (def.spawnEvery) {
      e.abilityTimer += dt;
      if (e.abilityTimer >= def.spawnEvery) {
        e.abilityTimer = 0;
        G.enemies.push(makeEnemy(def.spawnType, { d: Math.max(0, e.d - 20) }));
        addFloat(pointAt(G.path, e.d), 'spawns!', '#ff8877');
      }
    }
    if (def.teleportEvery) {
      e.abilityTimer += dt;
      if (e.abilityTimer >= def.teleportEvery) {
        e.abilityTimer = 0;
        e.d = Math.min(G.path.total - 1, e.d + def.teleportDist);
        addFloat(pointAt(G.path, e.d), '≠ blink', '#b39dff');
      }
    }
    if (def.hydra) {
      var lostPct = 1 - e.hp / e.maxHp;
      var stage = Math.floor(lostPct / 0.25);
      while (e.hydraStage < stage && e.hydraStage < 3) {
        e.hydraStage++;
        for (var h = 0; h < 3; h++) {
          var head = makeEnemy('jackal', { d: Math.max(0, e.d - h * 16), hpMult: 1.5 });
          head.label = '∞';
          G.enemies.push(head);
        }
        addFloat(pointAt(G.path, e.d), 'heads regrow!', '#7de8a0');
      }
    }

    e.d += enemySpeed(e) * dt;
    if (e.d >= G.path.total) {
      e.dead = true;
      e.leaked = true;
      var cost = def.boss ? 5 : 1;
      G.lives -= cost;
      if (def.leakSteal) {
        G.gold = Math.max(0, G.gold - def.leakSteal);
        addFloat({ x: W - 60, y: 40 }, '-' + def.leakSteal + 'g stolen!', '#ff7777');
      }
      AudioSys.hurt();
      if (G.lives <= 0) endGame(false);
    }
  }

  // ------------------------------------------------------------------
  // Towers
  // ------------------------------------------------------------------
  var towerId = 0;
  function makeTower(key, cx, cy) {
    var def = TOWERS[key];
    return {
      id: ++towerId,
      key: key,
      def: def,
      cx: cx, cy: cy,
      x: cx * CELL + CELL / 2,
      y: cy * CELL + CELL / 2,
      level: 0,
      cooldown: 0,
      invested: def.cost,
      lastTargetId: null,
      stack: 0,
      dmg: def.dmg,
      period: def.period,
      range: def.range,
      flash: 0,
    };
  }

  function applyLevel(t) {
    var lv = t.level;
    t.dmg = t.def.dmg * Math.pow(UPG.dmg, lv);
    t.period = t.def.period * Math.pow(UPG.period, lv);
    t.range = t.def.range === 9999 ? 9999 : t.def.range * Math.pow(UPG.range, lv);
  }

  function upgradeCost(t) {
    return Math.round(t.def.cost * UPG.costRatio * (t.level + 1));
  }

  function hasteFor(t) {
    var mult = 1;
    for (var i = 0; i < G.towers.length; i++) {
      var o = G.towers[i];
      if (o.def.aura === 'haste' && o !== t && dist(o.x, o.y, t.x, t.y) <= o.range) {
        mult += o.def.auraHaste + o.level * 0.08;
      }
    }
    return mult;
  }

  function pickTarget(t) {
    var best = null, bestVal = -1;
    for (var i = 0; i < G.enemies.length; i++) {
      var e = G.enemies[i];
      if (e.dead) continue;
      var p = pointAt(G.path, e.d);
      if (t.range < 9999 && dist(t.x, t.y, p.x, p.y) > t.range) continue;
      var val = (t.def.targeting === 'strong') ? e.hp : e.d;
      if (val > bestVal) { bestVal = val; best = e; }
    }
    return best;
  }

  function fireTower(t, target, dt) {
    var def = t.def;
    var tp = pointAt(G.path, target.d);

    if (def.beam) {
      // Ray from tower through target, extended; hits all enemies near the line.
      var dx = tp.x - t.x, dy = tp.y - t.y;
      var len = Math.max(1, Math.sqrt(dx * dx + dy * dy));
      var ux = dx / len, uy = dy / len;
      var reach = t.range * 1.7;
      var ex = t.x + ux * reach, ey = t.y + uy * reach;
      G.beams.push({ x1: t.x, y1: t.y, x2: ex, y2: ey, color: def.proj, ttl: 0.18 });
      for (var i = 0; i < G.enemies.length; i++) {
        var e = G.enemies[i];
        if (e.dead) continue;
        var p = pointAt(G.path, e.d);
        // distance from point to segment
        var vx = p.x - t.x, vy = p.y - t.y;
        var proj = vx * ux + vy * uy;
        if (proj < 0 || proj > reach) continue;
        var perp = Math.abs(vx * uy - vy * ux);
        if (perp <= e.r + 8) damageEnemy(e, t.dmg);
      }
      AudioSys.shoot();
      return;
    }

    var dmg = t.dmg;
    var opts = {};

    if (def.primeMult) {
      if (target.prime) { dmg *= def.primeMult; opts.ignoreArmor = true; }
    }
    if (def.hpPct) dmg += target.hp * (def.hpPct + t.level * 0.02);
    if (def.crit && Math.random() < (def.crit + t.level * 0.07)) {
      dmg *= def.critMult;
      opts.crit = true; opts.critMult = def.critMult;
    }
    if (t.key === 'add') {
      if (t.lastTargetId === target.id) t.stack = Math.min(20, t.stack + 2);
      else t.stack = 0;
      t.lastTargetId = target.id;
      dmg += t.stack;
    }

    G.projectiles.push({
      x: t.x, y: t.y, targetId: target.id, spd: 420,
      dmg: dmg, opts: opts, color: def.proj,
      splash: def.splash ? def.splash + t.level * 10 : 0,
      slow: def.slow ? { mult: def.slow - t.level * 0.08, dur: def.slowDur + t.level * 0.5 } : null,
      big: !!def.splash,
    });
    AudioSys.shoot();
    t.flash = 0.12;
  }

  function updateTower(t, dt) {
    if (t.def.period === 0) return; // aura towers
    t.flash = Math.max(0, t.flash - dt);
    t.cooldown -= dt * hasteFor(t);
    if (t.cooldown <= 0) {
      var target = pickTarget(t);
      if (target) {
        fireTower(t, target, dt);
        t.cooldown = t.period;
      }
    }
  }

  // ------------------------------------------------------------------
  // Projectiles / effects
  // ------------------------------------------------------------------
  function updateProjectile(pr, dt) {
    var target = null;
    for (var i = 0; i < G.enemies.length; i++) {
      if (G.enemies[i].id === pr.targetId && !G.enemies[i].dead) { target = G.enemies[i]; break; }
    }
    if (!target) { pr.dead = true; return; }
    var tp = pointAt(G.path, target.d);
    var d = dist(pr.x, pr.y, tp.x, tp.y);
    var step = pr.spd * dt;
    if (d <= step + target.r) {
      pr.dead = true;
      if (pr.splash) {
        AudioSys.boom();
        addParticles(tp.x, tp.y, '#ff9d66', 14);
        for (var j = 0; j < G.enemies.length; j++) {
          var e = G.enemies[j];
          if (e.dead) continue;
          var ep = pointAt(G.path, e.d);
          if (dist(tp.x, tp.y, ep.x, ep.y) <= pr.splash) damageEnemy(e, pr.dmg, pr.opts);
        }
      } else {
        damageEnemy(target, pr.dmg, pr.opts);
        if (pr.slow) target.slows.push({ mult: pr.slow.mult, until: G.time + pr.slow.dur });
      }
      return;
    }
    pr.x += (tp.x - pr.x) / d * step;
    pr.y += (tp.y - pr.y) / d * step;
  }

  function addFloat(p, text, color) {
    G.floats.push({ x: p.x, y: p.y - 14, text: text, color: color, ttl: 1.0 });
  }

  function addParticles(x, y, color, n) {
    for (var i = 0; i < n; i++) {
      var a = Math.random() * Math.PI * 2, v = 40 + Math.random() * 90;
      G.particles.push({ x: x, y: y, vx: Math.cos(a) * v, vy: Math.sin(a) * v, color: color, ttl: 0.4 + Math.random() * 0.3 });
    }
  }

  // ------------------------------------------------------------------
  // Waves
  // ------------------------------------------------------------------
  function startWave() {
    if (G.state !== 'build') return;
    var wave = era().waves[G.waveIdx];
    G.spawnQueue = [];
    var delay = 0;
    wave.forEach(function (grp) {
      for (var i = 0; i < grp.n; i++) {
        G.spawnQueue.push({ t: grp.t, at: delay });
        delay += grp.gap;
      }
      delay += 1.2;
    });
    G.spawnTimer = 0;
    G.state = 'wave';
    AudioSys.wave();
    updateHud();
  }

  function waveDone() {
    return G.spawnQueue.length === 0 && G.enemies.length === 0;
  }

  function onWaveCleared() {
    G.globalWave++;
    G.waveIdx++;
    G.score += 150;
    G.gold += 60 + G.globalWave * 6;
    if (G.waveIdx >= era().waves.length) {
      // Era complete
      G.score += 600;
      if (G.eraIdx >= ERAS.length - 1) { endGame(true); return; }
      // Refund all towers fully — the map changes with history.
      var refund = 0;
      G.towers.forEach(function (t) { refund += t.invested; });
      G.gold += refund;
      G.towers = [];
      G.selectedTower = null;
      G.eraIdx++;
      G.waveIdx = 0;
      loadEra();
      showMentor();
    } else {
      G.state = 'build';
    }
    updateHud();
  }

  function nextWavePreview() {
    if (G.waveIdx >= era().waves.length) return '';
    var counts = {};
    era().waves[G.waveIdx].forEach(function (g) {
      var nm = ENEMIES[g.t].name;
      counts[nm] = (counts[nm] || 0) + g.n;
    });
    return Object.keys(counts).map(function (k) { return counts[k] + '× ' + k; }).join(', ');
  }

  // ------------------------------------------------------------------
  // Era loading / rendering the background
  // ------------------------------------------------------------------
  var bgCanvas = document.createElement('canvas');
  bgCanvas.width = W; bgCanvas.height = H;

  function loadEra() {
    var e = era();
    G.path = buildPath(e.path);
    G.blocked = blockedCells(e.path);
    e.unlocks.forEach(function (k) { G.unlocked[k] = true; });
    CODEX[G.eraIdx].unlocked = true;
    drawBackground();
    buildShop();
  }

  function drawBackground() {
    var c = bgCanvas.getContext('2d');
    var pal = era().palette;
    // checkered ground
    for (var y = 0; y < ROWS; y++) {
      for (var x = 0; x < COLS; x++) {
        c.fillStyle = ((x + y) % 2 === 0) ? pal.bg : pal.bg2;
        c.fillRect(x * CELL, y * CELL, CELL, CELL);
      }
    }
    // era decorations (abstract, procedural)
    c.save();
    c.globalAlpha = 0.5;
    c.fillStyle = pal.deco;
    var id = era().id;
    for (var i = 0; i < 26; i++) {
      var dx = (i * 137 + 40) % W, dy = (i * 89 + 30) % H;
      if (G.blocked[Math.floor(dx / CELL) + ',' + Math.floor(dy / CELL)]) continue;
      c.beginPath();
      if (id === 'prehistory') {
        c.rect(dx, dy, 3, 12); c.rect(dx + 5, dy, 3, 12); // tally marks
      } else if (id === 'egypt') {
        c.moveTo(dx, dy + 12); c.lineTo(dx + 8, dy); c.lineTo(dx + 16, dy + 12); c.closePath(); // pyramids
      } else if (id === 'greece') {
        c.rect(dx, dy, 4, 14); c.rect(dx + 7, dy, 4, 14); // columns
      } else if (id === 'goldenage') {
        c.arc(dx, dy, 2.2, 0, Math.PI * 2); // stars
      } else {
        c.arc(dx, dy, 6, 0, Math.PI * 2); c.moveTo(dx - 10, dy); c.lineTo(dx + 10, dy); // orbits
      }
      c.fill();
    }
    c.restore();

    // path
    c.lineCap = 'round'; c.lineJoin = 'round';
    c.strokeStyle = pal.pathEdge; c.lineWidth = 40;
    strokePath(c);
    c.strokeStyle = pal.path; c.lineWidth = 32;
    strokePath(c);
    // dashed center line
    c.strokeStyle = 'rgba(255,255,255,0.18)'; c.lineWidth = 2;
    c.setLineDash([8, 10]);
    strokePath(c);
    c.setLineDash([]);
  }

  function strokePath(c) {
    var pts = G.path.pts;
    c.beginPath();
    c.moveTo(pts[0][0], pts[0][1]);
    for (var i = 1; i < pts.length; i++) c.lineTo(pts[i][0], pts[i][1]);
    c.stroke();
  }

  // ------------------------------------------------------------------
  // Canvas / drawing
  // ------------------------------------------------------------------
  var canvas = root.querySelector('canvas');
  canvas.width = W; canvas.height = H;
  var ctx = canvas.getContext('2d');

  function draw() {
    ctx.drawImage(bgCanvas, 0, 0);

    // placement ghost
    if (G.selectedShop && G.hoverCell) {
      var gx = G.hoverCell[0], gy = G.hoverCell[1];
      var ok = canPlace(gx, gy);
      ctx.save();
      ctx.globalAlpha = 0.35;
      ctx.fillStyle = ok ? '#7de8a0' : '#ff7777';
      ctx.fillRect(gx * CELL, gy * CELL, CELL, CELL);
      var def = TOWERS[G.selectedShop];
      if (def.range < 9999) {
        ctx.strokeStyle = ok ? '#7de8a0' : '#ff7777';
        ctx.lineWidth = 2;
        ctx.beginPath();
        ctx.arc(gx * CELL + CELL / 2, gy * CELL + CELL / 2, def.range, 0, Math.PI * 2);
        ctx.stroke();
      }
      ctx.restore();
    }

    // towers
    G.towers.forEach(drawTower);

    // selected tower range
    if (G.selectedTower && G.selectedTower.range < 9999) {
      ctx.save();
      ctx.strokeStyle = 'rgba(255,255,255,0.5)';
      ctx.lineWidth = 1.5;
      ctx.setLineDash([6, 6]);
      ctx.beginPath();
      ctx.arc(G.selectedTower.x, G.selectedTower.y, G.selectedTower.range, 0, Math.PI * 2);
      ctx.stroke();
      ctx.restore();
    }

    // enemies
    G.enemies.forEach(drawEnemy);

    // beams
    G.beams.forEach(function (b) {
      ctx.save();
      ctx.globalAlpha = Math.max(0, b.ttl / 0.18);
      ctx.strokeStyle = b.color;
      ctx.lineWidth = 4;
      ctx.beginPath(); ctx.moveTo(b.x1, b.y1); ctx.lineTo(b.x2, b.y2); ctx.stroke();
      ctx.restore();
    });

    // projectiles
    G.projectiles.forEach(function (p) {
      ctx.fillStyle = p.color;
      ctx.beginPath();
      ctx.arc(p.x, p.y, p.big ? 6 : 4, 0, Math.PI * 2);
      ctx.fill();
    });

    // particles
    G.particles.forEach(function (p) {
      ctx.save();
      ctx.globalAlpha = Math.max(0, p.ttl / 0.6);
      ctx.fillStyle = p.color;
      ctx.fillRect(p.x - 2, p.y - 2, 4, 4);
      ctx.restore();
    });

    // floating text
    ctx.font = 'bold 13px "Source Sans 3", sans-serif';
    ctx.textAlign = 'center';
    G.floats.forEach(function (f) {
      ctx.save();
      ctx.globalAlpha = Math.max(0, f.ttl);
      ctx.fillStyle = f.color;
      ctx.fillText(f.text, f.x, f.y - (1 - f.ttl) * 24);
      ctx.restore();
    });
  }

  function drawTower(t) {
    var def = t.def;
    ctx.save();
    ctx.translate(t.x, t.y);
    // base
    ctx.fillStyle = 'rgba(0,0,0,0.25)';
    ctx.beginPath(); ctx.arc(2, 4, 20, 0, Math.PI * 2); ctx.fill();
    ctx.fillStyle = def.color;
    ctx.strokeStyle = 'rgba(255,255,255,0.65)';
    ctx.lineWidth = 2;
    ctx.beginPath(); ctx.arc(0, 0, 19, 0, Math.PI * 2); ctx.fill(); ctx.stroke();
    if (t.flash > 0) {
      ctx.fillStyle = 'rgba(255,255,255,' + (t.flash * 4) + ')';
      ctx.beginPath(); ctx.arc(0, 0, 19, 0, Math.PI * 2); ctx.fill();
    }
    // aura ring
    if (def.aura) {
      ctx.strokeStyle = def.aura === 'slow' ? 'rgba(120,170,255,0.35)' : 'rgba(255,140,90,0.35)';
      ctx.lineWidth = 2;
      ctx.beginPath(); ctx.arc(0, 0, t.range, 0, Math.PI * 2); ctx.stroke();
    }
    // symbol
    ctx.fillStyle = '#fff';
    ctx.font = (def.sym.length > 2 ? 'bold 11px' : 'bold 17px') + ' "Fraunces", serif';
    ctx.textAlign = 'center'; ctx.textBaseline = 'middle';
    ctx.fillText(def.sym, 0, 1);
    // level pips
    for (var i = 0; i < t.level; i++) {
      ctx.fillStyle = '#ffd23f';
      ctx.beginPath(); ctx.arc(-8 + i * 8, 24, 3, 0, Math.PI * 2); ctx.fill();
    }
    ctx.restore();
  }

  function drawEnemy(e) {
    var p = pointAt(G.path, e.d);
    var def = e.def;
    var r = e.r + Math.sin(e.wobble) * 1.2;
    ctx.save();
    ctx.translate(p.x, p.y);
    if (def.ghost) ctx.globalAlpha = 0.65;
    // shadow
    ctx.fillStyle = 'rgba(0,0,0,0.25)';
    ctx.beginPath(); ctx.ellipse(0, r * 0.75, r * 0.9, r * 0.35, 0, 0, Math.PI * 2); ctx.fill();
    // body
    ctx.fillStyle = def.color;
    ctx.strokeStyle = e.prime ? '#e8ccff' : 'rgba(0,0,0,0.35)';
    ctx.lineWidth = e.prime ? 2.5 : 1.5;
    ctx.beginPath();
    if (def.boss) {
      // spiky boss silhouette
      for (var i = 0; i < 10; i++) {
        var a = (i / 10) * Math.PI * 2;
        var rr = r * (i % 2 === 0 ? 1.15 : 0.85);
        var x = Math.cos(a) * rr, y = Math.sin(a) * rr;
        if (i === 0) ctx.moveTo(x, y); else ctx.lineTo(x, y);
      }
      ctx.closePath();
    } else {
      ctx.arc(0, 0, r, 0, Math.PI * 2);
    }
    ctx.fill(); ctx.stroke();
    // eyes
    ctx.fillStyle = '#1c1c1c';
    ctx.beginPath(); ctx.arc(-r * 0.3, -r * 0.2, r * 0.14, 0, Math.PI * 2);
    ctx.arc(r * 0.3, -r * 0.2, r * 0.14, 0, Math.PI * 2); ctx.fill();
    // number / label — enemies literally wear their mathematics
    var label = e.label !== null ? e.label : (e.num !== null ? String(e.num) : '');
    if (label) {
      ctx.fillStyle = '#fff';
      ctx.font = 'bold ' + Math.max(9, r * 0.75) + 'px "JetBrains Mono", monospace';
      ctx.textAlign = 'center'; ctx.textBaseline = 'middle';
      ctx.fillText(label, 0, r * 0.35);
    }
    // hp bar
    var w = r * 2;
    ctx.fillStyle = 'rgba(0,0,0,0.5)';
    ctx.fillRect(-w / 2, -r - 9, w, 4);
    ctx.fillStyle = e.hp / e.maxHp > 0.4 ? '#7de8a0' : '#ff9d66';
    ctx.fillRect(-w / 2, -r - 9, w * Math.max(0, e.hp / e.maxHp), 4);
    ctx.restore();
  }

  // ------------------------------------------------------------------
  // Update loop
  // ------------------------------------------------------------------
  var lastTs = null;
  function frame(ts) {
    requestAnimationFrame(frame);
    if (lastTs === null) lastTs = ts;
    var dt = Math.min(0.05, (ts - lastTs) / 1000);
    lastTs = ts;
    if (G.paused || G.state === 'menu' || G.state === 'dialog' || G.state === 'gameover' || G.state === 'victory') {
      if (G.path) draw();
      return;
    }
    dt *= G.speed;
    G.time += dt;

    if (G.state === 'wave') {
      G.spawnTimer += dt;
      while (G.spawnQueue.length && G.spawnQueue[0].at <= G.spawnTimer) {
        var s = G.spawnQueue.shift();
        G.enemies.push(makeEnemy(s.t));
      }
    }

    G.enemies.forEach(function (e) { if (!e.dead) updateEnemy(e, dt); });
    G.enemies = G.enemies.filter(function (e) { return !e.dead; });
    G.towers.forEach(function (t) { updateTower(t, dt); });
    G.projectiles.forEach(function (p) { updateProjectile(p, dt); });
    G.projectiles = G.projectiles.filter(function (p) { return !p.dead; });
    G.beams.forEach(function (b) { b.ttl -= dt; });
    G.beams = G.beams.filter(function (b) { return b.ttl > 0; });
    G.floats.forEach(function (f) { f.ttl -= dt; });
    G.floats = G.floats.filter(function (f) { return f.ttl > 0; });
    G.particles.forEach(function (p) {
      p.ttl -= dt; p.x += p.vx * dt; p.y += p.vy * dt; p.vy += 160 * dt;
    });
    G.particles = G.particles.filter(function (p) { return p.ttl > 0; });

    if (G.state === 'wave' && waveDone()) onWaveCleared();

    draw();
    updateHud();
  }

  // ------------------------------------------------------------------
  // Placement / selection
  // ------------------------------------------------------------------
  function canPlace(cx, cy) {
    if (cx < 0 || cy < 0 || cx >= COLS || cy >= ROWS) return false;
    if (G.blocked[cx + ',' + cy]) return false;
    for (var i = 0; i < G.towers.length; i++) {
      if (G.towers[i].cx === cx && G.towers[i].cy === cy) return false;
    }
    return true;
  }

  function canvasPos(ev) {
    var rect = canvas.getBoundingClientRect();
    var x = (ev.clientX - rect.left) / rect.width * W;
    var y = (ev.clientY - rect.top) / rect.height * H;
    return { x: x, y: y };
  }

  canvas.addEventListener('mousemove', function (ev) {
    var p = canvasPos(ev);
    G.hoverCell = [Math.floor(p.x / CELL), Math.floor(p.y / CELL)];
  });
  canvas.addEventListener('mouseleave', function () { G.hoverCell = null; });

  canvas.addEventListener('click', function (ev) {
    if (G.state !== 'build' && G.state !== 'wave') return;
    var p = canvasPos(ev);
    var cx = Math.floor(p.x / CELL), cy = Math.floor(p.y / CELL);

    // Place a tower?
    if (G.selectedShop) {
      var def = TOWERS[G.selectedShop];
      if (canPlace(cx, cy) && G.gold >= def.cost) {
        G.gold -= def.cost;
        var t = makeTower(G.selectedShop, cx, cy);
        G.towers.push(t);
        AudioSys.place();
        if (!ev.shiftKey) G.selectedShop = null;
        G.selectedTower = t;
        buildShop();
        showTowerPanel();
        updateHud();
        return;
      }
    }
    // Select an existing tower?
    var picked = null;
    for (var i = 0; i < G.towers.length; i++) {
      if (G.towers[i].cx === cx && G.towers[i].cy === cy) { picked = G.towers[i]; break; }
    }
    G.selectedTower = picked;
    if (picked) G.selectedShop = null;
    buildShop();
    showTowerPanel();
  });

  // ------------------------------------------------------------------
  // DOM / HUD
  // ------------------------------------------------------------------
  function $(sel) { return root.querySelector(sel); }

  var hud = {
    lives: $('.mb-lives'), gold: $('.mb-gold'), wave: $('.mb-wave'),
    score: $('.mb-score'), eraName: $('.mb-era-name'),
    waveBtn: $('.mb-wave-btn'), preview: $('.mb-preview'),
    speedBtn: $('.mb-speed-btn'), pauseBtn: $('.mb-pause-btn'), muteBtn: $('.mb-mute-btn'),
  };

  function updateHud() {
    hud.lives.textContent = G.lives;
    hud.gold.textContent = Math.floor(G.gold);
    hud.score.textContent = G.score;
    hud.wave.textContent = Math.min(G.waveIdx + 1, era().waves.length) + '/' + era().waves.length;
    hud.eraName.textContent = era().name + ' · ' + era().years;
    hud.waveBtn.disabled = G.state !== 'build';
    hud.waveBtn.textContent = G.state === 'wave' ? 'Wave in progress…' : 'Send Wave ' + (G.waveIdx + 1);
    hud.preview.textContent = G.state === 'build' ? ('Next: ' + nextWavePreview()) : '';
    // shop affordability
    var btns = root.querySelectorAll('.mb-shop button');
    for (var i = 0; i < btns.length; i++) {
      var key = btns[i].dataset.tower;
      btns[i].classList.toggle('mb-poor', G.gold < TOWERS[key].cost);
      btns[i].classList.toggle('mb-selected', G.selectedShop === key);
    }
  }

  function buildShop() {
    var shop = $('.mb-shop');
    shop.innerHTML = '';
    Object.keys(TOWERS).forEach(function (key) {
      if (!G.unlocked[key]) return;
      var def = TOWERS[key];
      var b = document.createElement('button');
      b.type = 'button';
      b.dataset.tower = key;
      b.innerHTML = '<span class="mb-shop-sym" style="background:' + def.color + '">' + def.sym + '</span>' +
        '<span class="mb-shop-name">' + def.name + '</span>' +
        '<span class="mb-shop-cost">' + def.cost + 'g</span>';
      b.title = def.desc;
      b.addEventListener('click', function () {
        G.selectedShop = (G.selectedShop === key) ? null : key;
        G.selectedTower = null;
        showTowerPanel();
        updateHud();
      });
      shop.appendChild(b);
    });
  }

  function showTowerPanel() {
    var panel = $('.mb-info');
    if (G.selectedShop) {
      var def = TOWERS[G.selectedShop];
      panel.innerHTML =
        '<h4>' + def.name + ' — ' + def.cost + 'g</h4>' +
        '<p>' + def.desc + '</p>' +
        '<p class="mb-hist">' + def.hist + '</p>' +
        '<p class="mb-hint">Click a free tile to build. Hold Shift to place several.</p>';
      return;
    }
    if (!G.selectedTower) {
      panel.innerHTML = '<p class="mb-hint">Select a tower from the shop, or click a placed tower to upgrade it.</p>';
      return;
    }
    var t = G.selectedTower;
    var maxed = t.level >= 3;
    var cost = upgradeCost(t);
    var sell = Math.round(t.invested * SELL_RATIO);
    panel.innerHTML =
      '<h4>' + t.def.name + ' <span class="mb-lv">Lv ' + (t.level + 1) + '</span></h4>' +
      '<p>' + (t.def.period ? ('Damage ' + Math.round(t.dmg) + ' · every ' + t.period.toFixed(2) + 's') : 'Aura tower') +
      (t.range < 9999 ? (' · range ' + Math.round(t.range)) : ' · infinite range') + '</p>' +
      '<p class="mb-hist">' + t.def.hist + '</p>' +
      '<div class="mb-info-btns">' +
      (maxed ? '<button type="button" disabled>Max level</button>'
        : '<button type="button" class="mb-upg">Upgrade — ' + cost + 'g</button>') +
      '<button type="button" class="mb-sell">Sell — ' + sell + 'g</button>' +
      '</div>';
    var upg = panel.querySelector('.mb-upg');
    if (upg) upg.addEventListener('click', function () {
      if (G.gold >= cost && t.level < 3) {
        G.gold -= cost;
        t.invested += cost;
        t.level++;
        applyLevel(t);
        AudioSys.place();
        showTowerPanel(); updateHud();
      }
    });
    panel.querySelector('.mb-sell').addEventListener('click', function () {
      G.gold += sell;
      G.towers = G.towers.filter(function (x) { return x !== t; });
      G.selectedTower = null;
      showTowerPanel(); updateHud();
    });
  }

  // ------------------------------------------------------------------
  // Overlays: menu, mentor dialog, codex, leaderboard, end screen
  // ------------------------------------------------------------------
  var overlay = $('.mb-overlay');

  function showOverlay(html) {
    overlay.innerHTML = html;
    overlay.classList.add('mb-show');
  }
  function hideOverlay() { overlay.classList.remove('mb-show'); }

  function showMenu() {
    G.state = 'menu';
    showOverlay(
      '<div class="mb-card mb-menu">' +
      '<p class="mb-kicker">A tower defense across the history of mathematics</p>' +
      '<h3>Math Bastion</h3>' +
      '<p class="mb-sub">The History of Ideas</p>' +
      '<p>Chaos is marching on civilization. Your only weapons are the ideas humanity invented to survive: counting, fractions, primes, zero, algebra, coordinates, probability, calculus.</p>' +
      '<p>Five eras. Thirty waves. Every tower is a mathematical idea — discovered, like the originals, because you needed it.</p>' +
      '<button type="button" class="mb-btn mb-start">Begin in Prehistory</button>' +
      '<button type="button" class="mb-btn mb-ghost mb-lb-btn">Leaderboard</button>' +
      '</div>');
    overlay.querySelector('.mb-start').addEventListener('click', function () {
      startGame();
    });
    overlay.querySelector('.mb-lb-btn').addEventListener('click', function () { showLeaderboard(showMenu); });
  }

  function showMentor() {
    G.state = 'dialog';
    var m = era().mentor;
    showOverlay(
      '<div class="mb-card mb-mentor">' +
      '<p class="mb-kicker">' + era().name + ' · ' + era().years + '</p>' +
      '<div class="mb-mentor-head"><span class="mb-portrait">' + m.emoji + '</span><h3>' + m.name + '</h3></div>' +
      m.lines.map(function (l) { return '<p class="mb-quote">“' + l + '”</p>'; }).join('') +
      '<div class="mb-discovery">✦ Discovery unlocked: <strong>' + m.discovery + '</strong>' +
      '<span>New towers: ' + era().unlocks.map(function (k) { return TOWERS[k].name; }).join(', ') + '</span></div>' +
      '<button type="button" class="mb-btn mb-go">Defend the Bastion</button>' +
      '</div>');
    overlay.querySelector('.mb-go').addEventListener('click', function () {
      hideOverlay();
      G.state = 'build';
      updateHud();
    });
  }

  function showCodex() {
    var wasPaused = G.paused;
    G.paused = true;
    var rows = CODEX.map(function (c) {
      return '<div class="mb-codex-row ' + (c.unlocked ? '' : 'mb-locked') + '">' +
        '<h4>' + (c.unlocked ? c.title : '???') + ' <span>' + c.era + ' · ' + c.years + '</span></h4>' +
        '<p>' + (c.unlocked ? c.blurb : 'Reach this era to unlock its discovery.') + '</p></div>';
    }).join('');
    showOverlay('<div class="mb-card mb-codex"><h3>Discovery Codex</h3>' + rows +
      '<button type="button" class="mb-btn mb-close">Back to the walls</button></div>');
    overlay.querySelector('.mb-close').addEventListener('click', function () {
      G.paused = wasPaused;
      hideOverlay();
    });
  }

  function showLeaderboard(back) {
    showOverlay('<div class="mb-card"><h3>Leaderboard</h3><p class="mb-hint">Loading…</p></div>');
    fetch(URLS.leaderboard).then(function (r) { return r.json(); }).then(function (data) {
      var rows = data.scores.length
        ? data.scores.map(function (s, i) {
          return '<tr><td>' + (i + 1) + '</td><td>' + escapeHtml(s.name) + '</td><td>' + s.score +
            '</td><td>' + escapeHtml(s.era || '—') + '</td><td>' + (s.victory ? '👑' : s.waves + ' waves') + '</td></tr>';
        }).join('')
        : '<tr><td colspan="5">No scores yet — be the first.</td></tr>';
      showOverlay('<div class="mb-card"><h3>Leaderboard</h3>' +
        '<table class="mb-table"><thead><tr><th>#</th><th>Name</th><th>Score</th><th>Era reached</th><th>Result</th></tr></thead>' +
        '<tbody>' + rows + '</tbody></table>' +
        '<button type="button" class="mb-btn mb-close">Back</button></div>');
      overlay.querySelector('.mb-close').addEventListener('click', back);
    }).catch(function () {
      showOverlay('<div class="mb-card"><h3>Leaderboard</h3><p>Could not load scores.</p>' +
        '<button type="button" class="mb-btn mb-close">Back</button></div>');
      overlay.querySelector('.mb-close').addEventListener('click', back);
    });
  }

  function escapeHtml(s) {
    return String(s).replace(/[&<>"']/g, function (ch) {
      return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[ch];
    });
  }

  function endGame(victory) {
    if (G.state === 'gameover' || G.state === 'victory') return;
    G.state = victory ? 'victory' : 'gameover';
    G.score += G.lives * 100;
    if (victory) { G.score += 2000; AudioSys.fanfare(); }
    var title = victory ? 'Civilization Endures' : 'The Bastion Has Fallen';
    var msg = victory
      ? 'From tally bones to calculus — you rebuilt the whole history of mathematical ideas, and it held the wall. Final score: <strong>' + G.score + '</strong>.'
      : 'Chaos broke through in <strong>' + era().name + '</strong> (wave ' + (G.globalWave + 1) + '). Score: <strong>' + G.score + '</strong>. Every failed idea teaches the next one.';
    showOverlay('<div class="mb-card"><h3>' + title + '</h3><p>' + msg + '</p>' +
      '<div class="mb-submit"><input type="text" maxlength="20" placeholder="Your name" class="mb-name">' +
      '<button type="button" class="mb-btn mb-send">Submit score</button></div>' +
      '<button type="button" class="mb-btn mb-ghost mb-again">Play again</button></div>');
    overlay.querySelector('.mb-send').addEventListener('click', function () {
      if (G.scoreSubmitted) return;
      var name = overlay.querySelector('.mb-name').value.trim() || 'Anonymous';
      G.scoreSubmitted = true;
      fetch(URLS.submit, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', 'X-CSRFToken': URLS.csrf },
        body: JSON.stringify({
          name: name, score: G.score, waves: G.globalWave,
          era: era().name, victory: victory,
        }),
      }).finally(function () { showLeaderboard(function () { showEndAgain(); }); });
    });
    overlay.querySelector('.mb-again').addEventListener('click', resetGame);
  }

  function showEndAgain() {
    showOverlay('<div class="mb-card"><h3>Thanks for defending civilization</h3>' +
      '<button type="button" class="mb-btn mb-again">Play again</button></div>');
    overlay.querySelector('.mb-again').addEventListener('click', resetGame);
  }

  function resetGame() {
    G.eraIdx = 0; G.waveIdx = 0; G.globalWave = 0;
    G.lives = LIVES_START; G.gold = GOLD_START; G.score = 0;
    G.towers = []; G.enemies = []; G.projectiles = []; G.beams = [];
    G.floats = []; G.particles = []; G.spawnQueue = [];
    G.unlocked = {}; G.selectedShop = null; G.selectedTower = null;
    G.time = 0; G.scoreSubmitted = false; G.paused = false; G.speed = 1;
    hud.speedBtn.textContent = '▶ 1×';
    hud.pauseBtn.textContent = '⏸';
    CODEX.forEach(function (c) { c.unlocked = false; });
    startGame();
  }

  function startGame() {
    loadEra();
    showMentor();
    updateHud();
  }

  // ------------------------------------------------------------------
  // Control buttons
  // ------------------------------------------------------------------
  hud.waveBtn.addEventListener('click', startWave);
  hud.speedBtn.addEventListener('click', function () {
    G.speed = G.speed === 1 ? 2 : 1;
    hud.speedBtn.textContent = G.speed === 1 ? '▶ 1×' : '⏩ 2×';
  });
  hud.pauseBtn.addEventListener('click', function () {
    G.paused = !G.paused;
    hud.pauseBtn.textContent = G.paused ? '▶' : '⏸';
  });
  hud.muteBtn.addEventListener('click', function () {
    hud.muteBtn.textContent = AudioSys.toggleMute() ? '🔇' : '🔊';
  });
  $('.mb-codex-btn').addEventListener('click', showCodex);
  $('.mb-lb-hud-btn').addEventListener('click', function () {
    var wasPaused = G.paused;
    G.paused = true;
    showLeaderboard(function () { G.paused = wasPaused; hideOverlay(); });
  });

  // ------------------------------------------------------------------
  // Boot
  // ------------------------------------------------------------------
  loadEra();
  showMenu();
  updateHud();
  requestAnimationFrame(frame);
})();

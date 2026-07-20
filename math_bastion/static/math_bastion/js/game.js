/*
 * Math Bastion: an idle tower defense through the history of mathematics.
 * One bastion, attacked from every direction. Inspired by the idle-TD genre
 * ("The Tower"): a single auto-firing tower, live upgrade tabs, endless
 * scaling waves. Every era of the campaign is a chapter in the real
 * history of math, and advancing eras requires passing a short Math Trial
 * taught by a historical mentor.
 *
 * All art is drawn procedurally on canvas; audio is synthesized with
 * WebAudio. No third-party assets. (c) Eric Kvale, released with site source.
 */
(function () {
  'use strict';

  const root = document.getElementById('mb-game');
  if (!root) return;

  const URLS = {
    leaderboard: root.dataset.leaderboardUrl,
    submit: root.dataset.scoreUrl,
    store: root.dataset.storeUrl,
    wallet: root.dataset.walletUrl,
    purchase: root.dataset.purchaseUrl,
    csrf: root.dataset.csrf,
  };

  // ================================================================
  // Constants
  // ================================================================
  const W = 960, H = 600;
  const CX = W / 2, CY = H / 2;
  const BASTION_R = 36;
  const WAVES_PER_ERA = 10;
  const TRIAL_QUESTIONS = 3;
  const TRIAL_PASS = 2;

  const GEM_COST_REVIVE = 60;
  const GEM_COST_DOUBLER = 40;
  const GEMS_WELCOME = 30;
  const GEMS_ERA_CLEAR = 15;

  // ================================================================
  // Eras: the historical spine of the campaign.
  // ================================================================
  const ERAS = [
    {
      id: 'prehistory', name: 'Prehistoric Counting', years: 'c. 20,000 BCE',
      pal: { sky0: '#191512', sky1: '#2e2721', glow: '#e8b04a', deco: '#8a7355', star: '#e8d5b5' },
      mentor: {
        name: 'Onna, Keeper of the Tally Bone', emoji: '🦴',
        intro: 'The herds come at night, and no one remembers how many we drove off before. I cut a notch in this bone for each one. One notch, one beast. Counting is how we stop being surprised.',
        trial: 'Show me you can keep the tally. The tribe is watching.',
        discovery: 'Counting & Tally Marks',
        blurb: 'The Ishango bone (c. 20,000 BCE) carries some of the oldest known tally marks. Before numerals existed, humans matched one mark to one thing: the root idea of all arithmetic.',
      },
    },
    {
      id: 'egypt', name: 'Mesopotamia & Egypt', years: 'c. 3,000 BCE',
      pal: { sky0: '#241a0e', sky1: '#4a3418', glow: '#ffb84d', deco: '#c9a76a', star: '#ffe1a1' },
      mentor: {
        name: 'Ahmes, Scribe of the Rhind Papyrus', emoji: '📜',
        intro: 'The Nile flood erases every field boundary, every year, and the tax collector still comes. We survey with ropes and split grain into parts. Whoever masters fractions masters the harvest.',
        trial: 'The granary ledgers must balance. Compute as a scribe computes.',
        discovery: 'Fractions & Multiplication',
        blurb: 'Egyptian scribes like Ahmes (c. 1550 BCE) computed with unit fractions to divide bread and land; Babylonians pressed multiplication tables into clay in base 60, and their 60s survive in our minutes and degrees.',
      },
    },
    {
      id: 'greece', name: 'Ancient Greece', years: 'c. 500 BCE',
      pal: { sky0: '#101720', sky1: '#1d2a3a', glow: '#8fd7ff', deco: '#cfc6b2', star: '#e8f4ff' },
      mentor: {
        name: 'Euclid of Alexandria', emoji: '📐',
        intro: 'Anyone can see that a fact is true. The Greeks asked a harder question: can you prove it must be? From five simple postulates we will build defenses no chaos can argue with.',
        trial: 'A proof is a wall that cannot be breached. Lay your stones carefully.',
        discovery: 'Geometry, Proof & Primes',
        blurb: 'Euclid’s Elements (c. 300 BCE) organized geometry into proofs from axioms and showed there are infinitely many primes: numbers divisible only by 1 and themselves, the atoms of arithmetic.',
      },
    },
    {
      id: 'goldenage', name: 'India & the Islamic Golden Age', years: 'c. 800 CE',
      pal: { sky0: '#12102b', sky1: '#251d4d', glow: '#c9a4ff', deco: '#9d8fd0', star: '#efe6ff' },
      mentor: {
        name: 'Al-Khwarizmi of the House of Wisdom', emoji: '⭐',
        intro: 'In Baghdad we gathered every book we could find, Greek, Indian, Persian, and read them all. From India came a gift: a symbol for nothing. Zero. With it, and with al-jabr, the unknown itself becomes a thing you can hunt.',
        trial: 'Restore the balance. Solve for what is hidden.',
        discovery: 'Zero & Algebra',
        blurb: 'Brahmagupta (628 CE) gave rules for zero and negatives; Al-Khwarizmi’s book on al-jabr (c. 820 CE) named algebra, and Latin translations of his name gave us the word "algorithm."',
      },
    },
    {
      id: 'revolution', name: 'The Scientific Revolution', years: 'c. 1600–1700 CE',
      pal: { sky0: '#0d1a16', sky1: '#173229', glow: '#7dffb0', deco: '#d9cdae', star: '#eaffe8' },
      mentor: {
        name: 'Isaac Newton', emoji: '🍎',
        intro: 'Descartes taught us to give every point an address, two numbers, and geometry becomes algebra. I needed more: the mathematics of change itself. If I have seen further, it is by standing on the shoulders of giants.',
        trial: 'Measure the world in motion. Rates, points, chances.',
        discovery: 'Coordinates, Probability & Calculus',
        blurb: 'Descartes’ coordinates (1637) fused algebra with geometry; Pascal and Fermat founded probability (1654); Newton and Leibniz independently invented calculus, the mathematics of motion and change.',
      },
    },
    {
      id: 'frontier', name: 'The Infinite Frontier', years: 'beyond 1700 CE',
      pal: { sky0: '#070711', sky1: '#161233', glow: '#ff9de2', deco: '#8f8fd0', star: '#ffffff' },
      mentor: {
        name: 'Every mathematician yet to come', emoji: '∞',
        intro: 'Past this point mathematics never stops: infinities, imaginaries, computation itself. The waves no longer end. Hold the bastion as long as knowledge holds.',
        trial: '',
        discovery: 'Endless Mode',
        blurb: 'After Newton the story only accelerates: Euler, Gauss, Riemann, Noether, Ramanujan, Turing… Endless mode honors all of them. Waves scale forever.',
      },
    },
  ];

  // ================================================================
  // Upgrades: bought live during a run, The-Tower style.
  // era: trials that must be passed before it appears in the shop.
  // ================================================================
  const UPGRADES = [
    { id: 'dmg', tab: 'attack', era: 0, name: 'Tally Strike', icon: '𝍫', base: 15, growth: 1.32, max: 99,
      desc: lv => '+4 damage per notch. Now: ' + fmt(stat('dmg')), note: 'One notch, one beast.' },
    { id: 'rate', tab: 'attack', era: 0, name: 'Counting Rhythm', icon: '♩', base: 20, growth: 1.35, max: 30,
      desc: lv => '+7% attack speed. Now: ' + stat('rate').toFixed(2) + '/s', note: 'Chants kept early counts in time.' },
    { id: 'range', tab: 'attack', era: 0, name: 'Watch Fires', icon: '🔥', base: 18, growth: 1.34, max: 20,
      desc: lv => '+9 range. Now: ' + Math.round(stat('range')), note: 'See the herd before it sees you.' },
    { id: 'splash', tab: 'attack', era: 1, name: 'Multiplication Burst', icon: '×', base: 60, growth: 1.40, max: 12,
      desc: lv => lv === 0 ? 'Shots explode for area damage.' : 'Blast radius: ' + Math.round(stat('splash')), note: 'Babylonian clay held the first times tables.' },
    { id: 'crit', tab: 'attack', era: 2, name: 'Geometric Precision', icon: '△', base: 50, growth: 1.36, max: 20,
      desc: lv => '+2% critical chance. Now: ' + Math.round(stat('crit') * 100) + '% for ×' + stat('critMult').toFixed(1), note: 'Postulate 1: a straight line between any two points.' },
    { id: 'prime', tab: 'attack', era: 2, name: 'Prime Resonance', icon: 'ℙ', base: 70, growth: 1.40, max: 10,
      desc: lv => lv === 0 ? 'Pierce prime shells; bonus damage to primes.' : '×' + stat('prime').toFixed(2) + ' damage to primes, shells pierced', note: 'Euclid: there are infinitely many primes.' },
    { id: 'multi', tab: 'attack', era: 4, name: 'Cartesian Multishot', icon: '⌖', base: 260, growth: 2.10, max: 3,
      desc: lv => 'Fire at +1 target. Now: ' + (1 + lv) + ' targets', note: 'Every point has an address (x, y).' },
    { id: 'over', tab: 'attack', era: 4, name: 'Calculus Overdrive', icon: 'd/dx', base: 200, growth: 1.55, max: 8,
      desc: lv => lv === 0 ? 'Every 12s: burst of double fire rate.' : 'Overdrive lasts ' + stat('overDur').toFixed(1) + 's', note: 'The derivative: how fast things change.' },

    { id: 'hp', tab: 'defense', era: 0, name: 'Bastion Walls', icon: '🧱', base: 15, growth: 1.31, max: 99,
      desc: lv => '+30 max health. Now: ' + Math.round(stat('hpMax')), note: 'Jericho’s walls predate its pottery.' },
    { id: 'regen', tab: 'defense', era: 0, name: 'Mason’s Repair', icon: '🔨', base: 22, growth: 1.34, max: 40,
      desc: lv => '+0.7 health/s. Now: ' + stat('regen').toFixed(1) + '/s', note: 'Stone by stone, count by count.' },
    { id: 'armor', tab: 'defense', era: 0, name: 'Stone Facing', icon: '🛡', base: 30, growth: 1.38, max: 15,
      desc: lv => '+3% damage reduction. Now: ' + Math.round(stat('armor') * 100) + '%', note: 'Angled stone sheds the blow.' },
    { id: 'slow', tab: 'defense', era: 1, name: 'Fraction Field', icon: '½', base: 55, growth: 1.38, max: 10,
      desc: lv => lv === 0 ? 'Slow all enemies in range.' : 'Enemies slowed ' + Math.round((1 - stat('slow')) * 100) + '%', note: 'Half of a half is a quarter…' },
    { id: 'well', tab: 'defense', era: 3, name: 'Zero Well', icon: '0', base: 70, growth: 1.40, max: 8,
      desc: lv => lv === 0 ? 'Enemies near the bastion slow toward zero.' : 'Extra ' + Math.round((1 - stat('well')) * 100) + '% slow inside the well', note: 'Zero: the number that made nothing into something.' },

    { id: 'coin', tab: 'scholar', era: 0, name: 'Scribe’s Ledger', icon: '🪙', base: 20, growth: 1.36, max: 40,
      desc: lv => '+8% coins from kills. Now: +' + Math.round((stat('coin') - 1) * 100) + '%', note: 'Writing itself began as accounting.' },
    { id: 'tribute', tab: 'scholar', era: 0, name: 'Oral Tradition', icon: '🗣', base: 25, growth: 1.33, max: 40,
      desc: lv => '+' + Math.round(stat('tribute')) + ' coins each wave', note: 'Stories carried numbers before ink did.' },
    { id: 'solve', tab: 'scholar', era: 3, name: 'Al-Jabr Solve', icon: '𝑥', base: 80, growth: 1.45, max: 8,
      desc: lv => lv === 0 ? 'Instantly solve (kill) weakened enemies.' : 'Executes non-boss below ' + Math.round(stat('solve') * 100) + '% HP', note: 'Al-jabr: restoring balance to the equation.' },
    { id: 'interest', tab: 'scholar', era: 3, name: 'House of Wisdom', icon: '🏛', base: 90, growth: 1.50, max: 5,
      desc: lv => '+1% interest on held coins each wave. Now: ' + lv + '%', note: 'Baghdad paid translators in gold.' },
    { id: 'prob', tab: 'scholar', era: 4, name: 'Probability Engine', icon: '🎲', base: 60, growth: 1.40, max: 10,
      desc: lv => '+2% chance kills pay double. Now: ' + Math.round(stat('prob') * 100) + '%', note: 'Pascal and Fermat, arguing over dice, 1654.' },
  ];

  const TABS = [
    { id: 'attack', label: '⚔ Attack' },
    { id: 'defense', label: '🛡 Defense' },
    { id: 'scholar', label: '📖 Scholar' },
  ];

  // Workshop: permanent meta upgrades bought with Wisdom between runs.
  const WORKSHOP = [
    { id: 'wDmg', name: 'Ancestral Strength', desc: '+5% damage, permanently', base: 10, growth: 1.5, max: 20 },
    { id: 'wHp', name: 'Deep Foundations', desc: '+5% max health, permanently', base: 10, growth: 1.5, max: 20 },
    { id: 'wCoin', name: 'Trade Routes', desc: '+5% coins, permanently', base: 12, growth: 1.5, max: 20 },
    { id: 'wStart', name: 'War Chest', desc: '+50 starting coins', base: 8, growth: 1.45, max: 20 },
  ];

  // ================================================================
  // Enemies
  // ================================================================
  const ENEMIES = {
    numeral: { name: 'Wild Numeral', hp: 16, spd: 42, dmg: 6, coins: 5, r: 11, shape: 'blob', color: '#c05b4d', nums: [1, 4, 6, 8, 9] },
    jackal: { name: 'Swift Jackal', hp: 10, spd: 82, dmg: 4, coins: 4, r: 9, shape: 'tri', color: '#d99a3d', nums: [2, 3] },
    slime: { name: 'Fraction Slime', hp: 26, spd: 34, dmg: 8, coins: 6, r: 13, shape: 'blob', color: '#4da3c0', label: '1/1', splits: 'half' },
    half: { name: 'Half Slime', hp: 13, spd: 44, dmg: 4, coins: 3, r: 9, shape: 'blob', color: '#5fb3cf', label: '1/2', splits: 'quarter' },
    quarter: { name: 'Quarter Slime', hp: 6, spd: 54, dmg: 2, coins: 2, r: 6, shape: 'blob', color: '#79c4dc', label: '1/4' },
    prime: { name: 'Prime Shell', hp: 30, spd: 46, dmg: 9, coins: 9, r: 12, shape: 'hex', color: '#8d5fc0', prime: true, shell: 0.25, nums: [2, 3, 5, 7, 11, 13] },
    golem: { name: 'Composite Golem', hp: 70, spd: 26, dmg: 14, coins: 12, r: 16, shape: 'hex', color: '#7d7d6e', factors: [[2, 2, 3], [2, 3, 3], [2, 2, 5], [2, 2, 2, 3]] },
    factorling: { name: 'Factorling', hp: 9, spd: 62, dmg: 3, coins: 2, r: 7, shape: 'hex', color: '#9a9a88', prime: true },
    ghost: { name: 'Negative Spirit', hp: 20, spd: 68, dmg: 4, coins: 8, r: 11, shape: 'ghost', color: '#5a6b9e', ghost: true, steal: 18, nums: [-1, -2, -3, -5] },
    chaos: { name: 'Chaos Equation', hp: 42, spd: 46, dmg: 12, coins: 11, r: 12, shape: 'spark', color: '#b04a8f', chaotic: true, label: '?!' },
    boss_mammoth: { name: 'Mammoth of Ignorance', hp: 380, spd: 17, dmg: 45, coins: 90, r: 27, shape: 'boss', color: '#8a6f5a', boss: true, label: '?' },
    boss_sphinx: { name: 'Sphinx of Riddles', hp: 520, spd: 19, dmg: 50, coins: 120, r: 26, shape: 'boss', color: '#c2a24e', boss: true, label: '?', spawnEvery: 4, spawnType: 'jackal' },
    boss_drake: { name: 'Polynomial Drake', hp: 700, spd: 21, dmg: 55, coins: 150, r: 27, shape: 'boss', color: '#3e7d5a', boss: true, label: 'xⁿ', regen: 6 },
    boss_djinn: { name: 'Chaos Djinn', hp: 900, spd: 24, dmg: 60, coins: 190, r: 25, shape: 'boss', color: '#6a4ac2', boss: true, label: '≠', blinkEvery: 3.5, blinkDist: 55 },
    boss_hydra: { name: 'The Infinite Hydra', hp: 1300, spd: 17, dmg: 70, coins: 280, r: 30, shape: 'boss', color: '#345e46', boss: true, label: '∞', hydra: true },
  };
  const BOSS_ORDER = ['boss_mammoth', 'boss_sphinx', 'boss_drake', 'boss_djinn', 'boss_hydra'];

  // Which basic enemies appear per era (weights).
  const ERA_SPAWNS = [
    [['numeral', 5], ['jackal', 2]],
    [['numeral', 4], ['jackal', 3], ['slime', 3]],
    [['numeral', 3], ['jackal', 2], ['slime', 2], ['prime', 3], ['golem', 2]],
    [['jackal', 2], ['slime', 2], ['prime', 3], ['golem', 2], ['ghost', 3]],
    [['prime', 3], ['golem', 2], ['ghost', 2], ['chaos', 3], ['slime', 2]],
    [['prime', 3], ['golem', 3], ['ghost', 3], ['chaos', 3], ['slime', 2], ['jackal', 2]],
  ];

  // ================================================================
  // Math Trials: procedural question generators per era.
  // ================================================================
  function ri(a, b) { return a + Math.floor(Math.random() * (b - a + 1)); }
  function shuffle(arr) {
    for (let i = arr.length - 1; i > 0; i--) {
      const j = Math.floor(Math.random() * (i + 1));
      [arr[i], arr[j]] = [arr[j], arr[i]];
    }
    return arr;
  }
  function mcq(q, answer, wrongs, explain) {
    const opts = shuffle([answer].concat(wrongs.slice(0, 3)));
    return { q, opts: opts.map(String), answer: opts.indexOf(answer), explain };
  }

  const QUESTION_GENS = [
    // Era 0: counting, addition, subtraction
    () => {
      const kind = ri(0, 2);
      if (kind === 0) {
        const a = ri(4, 9), b = ri(3, 9);
        return mcq('Onna cut ' + a + ' notches at dusk and ' + b + ' more at dawn. How many beasts in all?',
          a + b, [a + b + 1, a + b - 1, a + b + 2],
          a + ' + ' + b + ' = ' + (a + b) + '. One notch for one beast: matching marks to things is the oldest arithmetic.');
      }
      if (kind === 1) {
        const a = ri(9, 16), b = ri(2, 7);
        return mcq('The tally shows ' + a + ' beasts, but ' + b + ' were driven off. How many remain?',
          a - b, [a - b + 1, a - b - 1, a - b + 2],
          a + ' − ' + b + ' = ' + (a - b) + '. Crossing out notches was the first subtraction.');
      }
      const g = ri(3, 5), n = ri(3, 5);
      return mcq('Notches come in groups of ' + g + '. You count ' + n + ' full groups. How many notches?',
        g * n, [g * n + g, g * n - g, g * n + 1],
        n + ' groups of ' + g + ' is ' + g * n + '. Grouping tallies was the first step toward multiplication.');
    },
    // Era 1: fractions & multiplication
    () => {
      const kind = ri(0, 2);
      if (kind === 0) {
        const a = ri(3, 9), b = ri(3, 9);
        return mcq('The granary ledger needs ' + a + ' rows of ' + b + ' jars. How many jars?',
          a * b, [a * b + a, a * b - b, a * b + 2],
          a + ' × ' + b + ' = ' + (a * b) + '. Babylonian scribes kept whole tables of these on clay.');
      }
      if (kind === 1) {
        const d = [2, 3, 4][ri(0, 2)], m = ri(2, 5), n = d * m;
        const w = { 2: 'half', 3: 'third', 4: 'quarter' }[d];
        return mcq('A ' + w + ' of ' + n + ' loaves goes to the temple. How many loaves is that?',
          m, [m + 1, m + 2, m + d],
          n + ' ÷ ' + d + ' = ' + m + '. Egyptians wrote every fraction as unit fractions: 1/2, 1/3, 1/4…');
      }
      const d1 = ri(2, 4), d2 = d1 + ri(1, 3);
      return mcq('Two workers are paid in bread: one gets 1/' + d1 + ' of a loaf, the other 1/' + d2 + '. Who gets more?',
        '1/' + d1, ['1/' + d2, 'equal shares', 'cannot be known'],
        'Cutting a loaf into fewer pieces makes bigger pieces: 1/' + d1 + ' > 1/' + d2 + '.');
    },
    // Era 2: primes & geometry
    () => {
      const kind = ri(0, 2);
      if (kind === 0) {
        const primes = [5, 7, 11, 13, 17, 19];
        const comps = shuffle([4, 6, 8, 9, 10, 12, 14, 15, 16, 18].slice());
        const p = primes[ri(0, primes.length - 1)];
        return mcq('Which of these numbers is prime, divisible only by 1 and itself?',
          p, [comps[0], comps[1], comps[2]],
          p + ' has no divisors besides 1 and ' + p + '. Euclid proved the primes never run out.');
      }
      if (kind === 1) {
        const a = ri(30, 80), b = ri(30, 80);
        return mcq('A triangle has angles of ' + a + '° and ' + b + '°. What is the third angle?',
          180 - a - b, [180 - a - b + 10, 180 - a - b - 10, 90],
          'Angles of a triangle sum to 180°: 180 − ' + a + ' − ' + b + ' = ' + (180 - a - b) + '°. Proved in Euclid’s Elements, Book I.');
      }
      const f = [2, 3, 5][ri(0, 2)], m = [7, 11, 13][ri(0, 2)], n = f * m;
      return mcq('The golem is the number ' + n + '. Which prime divides it evenly?',
        f, [f === 2 ? 3 : 2, f === 5 ? 3 : 5, 17],
        n + ' = ' + f + ' × ' + m + '. Every whole number breaks into prime factors, its atoms.');
    },
    // Era 3: zero, negatives, algebra
    () => {
      const kind = ri(0, 2);
      if (kind === 0) {
        const x = ri(3, 12), a = ri(2, 9);
        return mcq('Al-jabr: restore the balance in  x + ' + a + ' = ' + (x + a) + '.  What is x?',
          x, [x + 1, x + 2, x + a],
          'Take ' + a + ' from both sides: x = ' + x + '. "Al-jabr" means exactly this restoring of balance.');
      }
      if (kind === 1) {
        const a = ri(2, 9), b = a + ri(1, 9);
        return mcq('A merchant is ' + a + ' coins in debt (−' + a + ') and earns ' + b + ' coins. Where does he stand?',
          b - a, [a - b, b + a, 0],
          '−' + a + ' + ' + b + ' = ' + (b - a) + '. Brahmagupta wrote the rules for debts (negatives) in 628 CE.');
      }
      const n = ri(3, 99);
      return mcq('What is ' + n + ' × 0?',
        0, [n, 1, -n],
        'Anything times zero is zero, one of Brahmagupta’s rules that made zero a true number.');
    },
    // Era 4: coordinates, rates, probability
    () => {
      const kind = ri(0, 2);
      if (kind === 0) {
        const t = ri(2, 6), v = ri(6, 12);
        return mcq('A cannonball travels ' + (v * t) + ' leagues in ' + t + ' hours. What is its speed?',
          v + ' per hour', [(v + 1) + ' per hour', (v - 1) + ' per hour', (v * t) + ' per hour'],
          (v * t) + ' ÷ ' + t + ' = ' + v + ' leagues per hour. A rate of change: the seed of calculus.');
      }
      if (kind === 1) {
        const triples = [[3, 4, 5], [6, 8, 10], [5, 12, 13]], tr = triples[ri(0, 2)];
        return mcq('On Descartes’ grid, walk ' + tr[0] + ' east and ' + tr[1] + ' north. How far are you from the start, in a straight line?',
          tr[2], [tr[0] + tr[1], tr[2] + 1, tr[2] - 1],
          '√(' + tr[0] + '² + ' + tr[1] + '²) = ' + tr[2] + '. Pythagoras, reborn as coordinate geometry.');
      }
      return mcq('Pascal rolls a fair six-sided die. What is the chance of an even number?',
        '1/2', ['1/6', '1/3', '2/3'],
        'Three faces of six are even: 3/6 = 1/2. Probability began with Pascal and Fermat’s dice letters, 1654.');
    },
  ];

  // ================================================================
  // Persistence (meta progression + wallet cache)
  // ================================================================
  const SAVE_KEY = 'mathbastion.v2';
  const META_DEFAULT = {
    deviceKey: null, wisdom: 0, workshop: {}, gems: 0, welcomed: false,
    bestWave: 0, erasCleared: [], muted: false,
  };
  let META = META_DEFAULT;
  try {
    META = Object.assign({}, META_DEFAULT, JSON.parse(localStorage.getItem(SAVE_KEY) || '{}'));
  } catch (e) { /* fresh start */ }
  if (!META.deviceKey) {
    META.deviceKey = (window.crypto && crypto.randomUUID) ? crypto.randomUUID()
      : 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, c => {
          const r = Math.random() * 16 | 0; return (c === 'x' ? r : (r & 0x3 | 0x8)).toString(16);
        });
  }
  if (!META.welcomed) { META.gems += GEMS_WELCOME; META.welcomed = true; }
  function saveMeta() {
    try { localStorage.setItem(SAVE_KEY, JSON.stringify(META)); } catch (e) { /* private mode */ }
  }
  saveMeta();

  function api(url, body) {
    return fetch(url, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', 'X-CSRFToken': URLS.csrf },
      body: JSON.stringify(body),
    }).then(r => r.json());
  }
  // Best-effort wallet sync; local META.gems stays authoritative until real
  // payments land (then the server wallet becomes the source of truth).
  if (URLS.wallet) api(URLS.wallet, { device_key: META.deviceKey }).catch(() => {});

  // ================================================================
  // Audio: tiny synthesizer
  // ================================================================
  const AudioSys = (() => {
    let ctx = null, muted = !!META.muted;
    function ensure() {
      if (!ctx) { try { ctx = new (window.AudioContext || window.webkitAudioContext)(); } catch (e) { muted = true; } }
      if (ctx && ctx.state === 'suspended') ctx.resume();
    }
    function tone(freq, dur, type, vol, slide) {
      if (muted) return; ensure(); if (!ctx) return;
      const o = ctx.createOscillator(), g = ctx.createGain();
      o.type = type || 'square'; o.frequency.value = freq;
      if (slide) o.frequency.exponentialRampToValueAtTime(Math.max(30, freq + slide), ctx.currentTime + dur);
      g.gain.value = vol || 0.04;
      g.gain.exponentialRampToValueAtTime(0.0001, ctx.currentTime + dur);
      o.connect(g); g.connect(ctx.destination);
      o.start(); o.stop(ctx.currentTime + dur);
    }
    return {
      shoot: () => tone(560, 0.06, 'square', 0.018, -160),
      boom: () => tone(110, 0.22, 'sawtooth', 0.05, -50),
      coin: () => { tone(880, 0.08, 'triangle', 0.035); tone(1320, 0.1, 'triangle', 0.025); },
      hurt: () => tone(150, 0.28, 'sawtooth', 0.06, -70),
      buy: () => { tone(520, 0.08, 'triangle', 0.05); tone(780, 0.1, 'triangle', 0.04); },
      wrong: () => tone(180, 0.35, 'sawtooth', 0.05, -40),
      right: () => [660, 880].forEach((f, i) => setTimeout(() => tone(f, 0.15, 'triangle', 0.05), i * 90)),
      fanfare: () => [523, 659, 784, 1046].forEach((f, i) => setTimeout(() => tone(f, 0.2, 'triangle', 0.055), i * 120)),
      gem: () => [1046, 1568].forEach((f, i) => setTimeout(() => tone(f, 0.12, 'sine', 0.05), i * 70)),
      toggleMute: () => { muted = !muted; META.muted = muted; saveMeta(); return muted; },
      isMuted: () => muted,
    };
  })();

  // ================================================================
  // Run state
  // ================================================================
  const G = {
    state: 'menu',       // menu | run | trial | gameover
    wave: 0,             // completed waves
    eraIdx: 0,
    trialsPassed: 0,     // gates era advancement
    coins: 0, score: 0, speed: 1, paused: false,
    hp: 0, hpMax: 100,
    levels: {},          // upgrade id -> level
    enemies: [], projectiles: [], particles: [], floats: [],
    spawnLeft: 0, spawnTimer: 0, interTimer: 0, waveActive: false,
    currentComp: null, awaitTrial: false,
    turretA: 0, shake: 0, time: 0,
    overTimer: 0, overActive: 0,
    doubler: false, revived: false, wisdomGain: 0,
    kills: 0,
  };

  function eraForWave(w) { return Math.min(Math.floor(w / WAVES_PER_ERA), ERAS.length - 1); }
  function era() { return ERAS[G.eraIdx]; }
  function wLv(id) { return META.workshop[id] || 0; }
  function lv(id) { return G.levels[id] || 0; }

  // Derived stats
  function stat(id) {
    switch (id) {
      case 'dmg': return (12 + 4 * lv('dmg')) * (1 + 0.05 * wLv('wDmg')) * (G.overActive > 0 ? 1.15 : 1);
      case 'rate': return 1.0 * Math.pow(1.07, lv('rate')) * (G.overActive > 0 ? 2 : 1);
      case 'range': return 230 + 9 * lv('range');
      case 'splash': return lv('splash') ? 30 + 14 * lv('splash') : 0;
      case 'crit': return 0.03 + 0.02 * lv('crit');
      case 'critMult': return 2.5 + 0.1 * lv('crit');
      case 'prime': return lv('prime') ? 1.5 + 0.35 * lv('prime') : 1;
      case 'multi': return 1 + lv('multi');
      case 'overDur': return lv('over') ? 2.5 + 0.5 * lv('over') : 0;
      case 'hpMax': return (100 + 30 * lv('hp')) * (1 + 0.05 * wLv('wHp'));
      case 'regen': return 1 + 0.7 * lv('regen');
      case 'armor': return Math.min(0.45, 0.03 * lv('armor'));
      case 'slow': return lv('slow') ? 1 - (0.08 + 0.04 * lv('slow')) : 1;
      case 'well': return lv('well') ? 1 - (0.10 + 0.05 * lv('well')) : 1;
      case 'coin': return (1 + 0.08 * lv('coin')) * (1 + 0.05 * wLv('wCoin')) * (G.doubler ? 2 : 1);
      case 'tribute': return 8 + 4 * lv('tribute');
      case 'solve': return lv('solve') ? 0.05 + 0.02 * lv('solve') : 0;
      case 'interest': return 0.01 * lv('interest');
      case 'prob': return 0.02 * lv('prob');
    }
    return 0;
  }
  function fmt(n) {
    if (n >= 1e6) return (n / 1e6).toFixed(1) + 'M';
    if (n >= 1e4) return (n / 1e3).toFixed(1) + 'K';
    return String(Math.round(n));
  }
  function upgCost(u) { return Math.round(u.base * Math.pow(u.growth, lv(u.id))); }
  function workCost(w) { return Math.round(w.base * Math.pow(w.growth, wLv(w.id))); }

  // ================================================================
  // Enemies (radial)
  // ================================================================
  let enemyId = 0;
  function hpScale() { return Math.pow(1.13, G.wave) * (1 + 0.08 * Math.max(0, G.wave - 50)); }
  function coinScale() { return Math.pow(1.045, G.wave); }

  function spawnEnemy(type, opts = {}) {
    const def = ENEMIES[type];
    const angle = opts.angle !== undefined ? opts.angle : Math.random() * Math.PI * 2;
    const e = {
      id: ++enemyId, type, def,
      hp: def.hp * hpScale() * (opts.hpMult || 1),
      maxHp: def.hp * hpScale() * (opts.hpMult || 1),
      angle,
      dist: opts.dist !== undefined ? opts.dist : Math.hypot(CX, CY) * 0.98 + Math.random() * 50,
      wobA: Math.random() * Math.PI * 2,
      drift: (Math.random() - 0.5) * 0.14,
      chaosT: 0, chaosBoost: 1, abilityT: 0, hydraStage: 0,
      flash: 0, dead: false,
      num: def.nums ? def.nums[ri(0, def.nums.length - 1)] : null,
      label: def.label || null,
      factors: def.factors ? def.factors[ri(0, def.factors.length - 1)] : null,
    };
    if (e.factors) e.num = e.factors.reduce((a, b) => a * b, 1);
    G.enemies.push(e);
    return e;
  }
  function enemyPos(e) {
    const wob = Math.sin(e.wobA) * 4;
    return { x: CX + Math.cos(e.angle) * (e.dist + wob), y: CY + Math.sin(e.angle) * (e.dist + wob) };
  }

  function updateEnemy(e, dt) {
    const def = e.def;
    e.wobA += dt * 5;
    e.flash = Math.max(0, e.flash - dt);
    e.angle += e.drift * dt;

    if (def.chaotic) {
      e.chaosT -= dt;
      if (e.chaosT <= 0) { e.chaosBoost = Math.random() < 0.4 ? 2.4 : 1; e.chaosT = 0.5 + Math.random() * 1.1; }
    }
    if (def.spawnEvery) {
      e.abilityT += dt;
      if (e.abilityT >= def.spawnEvery) {
        e.abilityT = 0;
        spawnEnemy(def.spawnType, { angle: e.angle + (Math.random() - 0.5) * 0.6, dist: e.dist });
        addFloat(enemyPos(e), 'spawns!', '#ff9d88');
      }
    }
    if (def.blinkEvery) {
      e.abilityT += dt;
      if (e.abilityT >= def.blinkEvery) {
        e.abilityT = 0;
        e.dist = Math.max(BASTION_R + 30, e.dist - def.blinkDist);
        addFloat(enemyPos(e), '≠ blink', '#c9a4ff');
      }
    }
    if (def.regen) e.hp = Math.min(e.maxHp, e.hp + def.regen * hpScale() * dt * 0.1);
    if (def.hydra) {
      const stage = Math.floor((1 - e.hp / e.maxHp) / 0.25);
      while (e.hydraStage < stage && e.hydraStage < 3) {
        e.hydraStage++;
        for (let h = 0; h < 3; h++) {
          const head = spawnEnemy('jackal', { angle: e.angle + (h - 1) * 0.3, dist: e.dist + 10, hpMult: 1.6 });
          head.label = '∞';
        }
        addFloat(enemyPos(e), 'heads regrow!', '#7de8a0');
      }
    }

    // Movement with slow fields
    let mult = e.chaosBoost;
    if (lv('slow') && e.dist < stat('range')) mult *= stat('slow');
    if (lv('well') && e.dist < BASTION_R + 110) mult *= stat('well');
    e.dist -= def.spd * mult * dt;

    // Contact with the bastion
    if (e.dist <= BASTION_R + def.r * 0.4) {
      e.dead = true;
      const dmg = def.dmg * (1 + 0.05 * G.wave) * (1 - stat('armor'));
      G.hp -= dmg;
      G.shake = Math.min(14, G.shake + (def.boss ? 12 : 4));
      const p = enemyPos(e);
      addParticles(p.x, p.y, def.color, def.boss ? 30 : 10);
      addFloat({ x: CX, y: CY - BASTION_R - 16 }, '-' + Math.round(dmg), '#ff7777');
      if (def.steal) {
        const stolen = Math.min(G.coins, Math.round(def.steal * coinScale()));
        G.coins -= stolen;
        if (stolen > 0) addFloat(p, '-' + stolen + ' coins!', '#ffb84d');
      }
      AudioSys.hurt();
      if (G.hp <= 0) onDeath();
    }
  }

  function damageEnemy(e, amount, opts = {}) {
    if (e.dead) return;
    const def = e.def;
    if (def.shell && lv('prime') === 0) amount *= def.shell;
    if (def.prime) amount *= stat('prime');
    e.hp -= amount;
    e.flash = 0.1;
    const p = enemyPos(e);
    if (opts.crit) addFloat(p, 'CRIT ' + fmt(amount), '#ffd23f');
    else if (Math.random() < 0.2) addFloat(p, fmt(amount), 'rgba(255,255,255,0.75)');
    // Al-Jabr Solve: execute weakened non-boss enemies.
    if (!def.boss && stat('solve') > 0 && e.hp > 0 && e.hp / e.maxHp < stat('solve')) {
      e.hp = 0;
      addFloat(p, '𝑥 solved!', '#ffe97a');
    }
    if (e.hp <= 0) killEnemy(e);
  }

  function killEnemy(e) {
    e.dead = true;
    G.kills++;
    const def = e.def;
    let coins = Math.max(1, Math.round(def.coins * coinScale() * stat('coin')));
    if (Math.random() < stat('prob')) { coins *= 2; addFloat(enemyPos(e), '🎲 double!', '#b1e6a3'); }
    G.coins += coins;
    G.score += Math.round(def.coins * 10 * (1 + G.wave * 0.1));
    const p = enemyPos(e);
    addParticles(p.x, p.y, def.color, def.boss ? 34 : 8);
    addFloat(p, '+' + coins, '#f5d76e');
    if (!def.boss && Math.random() < 0.3) AudioSys.coin();

    if (def.splits) {
      for (let i = 0; i < 2; i++) spawnEnemy(def.splits, { angle: e.angle + (i ? 0.12 : -0.12), dist: e.dist });
    }
    if (e.factors) {
      e.factors.forEach((f, i) => {
        const child = spawnEnemy('factorling', { angle: e.angle + (i - e.factors.length / 2) * 0.1, dist: e.dist + 6 });
        child.num = f;
      });
    }
    if (def.boss) { AudioSys.fanfare(); G.shake = Math.min(16, G.shake + 10); }
    markUpgradesDirty();
  }

  // ================================================================
  // Waves: continuous, endless scaling.
  // ================================================================
  function waveComposition(w) {
    // w is 1-based wave number
    const eIdx = Math.min(eraForWave(w - 1), ERA_SPAWNS.length - 1);
    const count = Math.min(34, 6 + Math.floor(w * 0.9));
    const gap = Math.max(0.28, 1.0 - w * 0.012);
    return { pool: ERA_SPAWNS[eIdx], count, gap, boss: w % WAVES_PER_ERA === 0 };
  }
  function pickWeighted(pool) {
    let total = 0;
    pool.forEach(p => { total += p[1]; });
    let roll = Math.random() * total;
    for (const p of pool) { roll -= p[1]; if (roll <= 0) return p[0]; }
    return pool[0][0];
  }

  function startNextWave() {
    const w = G.wave + 1;
    const comp = waveComposition(w);
    G.waveActive = true;
    G.spawnLeft = comp.count;
    G.spawnTimer = 0;
    G.currentComp = comp;
    if (comp.boss) {
      const bossKey = BOSS_ORDER[Math.min(eraForWave(w - 1), BOSS_ORDER.length - 1)];
      const scale = 1 + Math.max(0, (w - 50)) * 0.25;
      const b = spawnEnemy(bossKey, { hpMult: scale });
      addFloat({ x: CX, y: 90 }, '⚠ ' + b.def.name + ' approaches!', '#ff9d66');
    }
  }

  function onWaveCleared() {
    G.wave++;
    G.waveActive = false;
    G.interTimer = 1.4;
    G.score += 100 + G.wave * 12;
    let bonus = Math.round(stat('tribute') * coinScale());
    bonus += Math.round(G.coins * stat('interest'));
    G.coins += bonus;
    if (bonus > 0) addFloat({ x: CX, y: CY - 70 }, '+' + bonus + ' tribute', '#f5d76e');
    META.bestWave = Math.max(META.bestWave, G.wave);
    saveMeta();

    // Era gate: after each era's boss wave a Math Trial is required,
    // until the endless frontier, which has no more gates.
    const targetEra = eraForWave(G.wave);
    if (targetEra > G.trialsPassed && G.trialsPassed < QUESTION_GENS.length) {
      G.awaitTrial = true;
      openTrial();
    }
    markUpgradesDirty();
  }

  function updateSpawning(dt) {
    if (G.awaitTrial) return;
    if (!G.waveActive) {
      G.interTimer -= dt;
      if (G.interTimer <= 0) startNextWave();
      return;
    }
    if (G.spawnLeft > 0) {
      G.spawnTimer -= dt;
      if (G.spawnTimer <= 0) {
        spawnEnemy(pickWeighted(G.currentComp.pool));
        G.spawnLeft--;
        G.spawnTimer = G.currentComp.gap;
      }
    } else if (G.enemies.length === 0) {
      onWaveCleared();
    }
  }

  // ================================================================
  // Bastion combat
  // ================================================================
  let fireCooldown = 0;
  function updateCombat(dt) {
    if (lv('over')) {
      if (G.overActive > 0) {
        G.overActive -= dt;
      } else {
        G.overTimer += dt;
        if (G.overTimer >= 12) {
          G.overTimer = 0;
          G.overActive = stat('overDur');
          addFloat({ x: CX, y: CY - 54 }, 'd/dx OVERDRIVE', '#7dffb0');
        }
      }
    }
    fireCooldown -= dt * stat('rate');
    if (fireCooldown > 0) return;
    const range = stat('range');
    const targets = G.enemies
      .filter(e => !e.dead && e.dist <= range)
      .sort((a, b) => a.dist - b.dist)
      .slice(0, stat('multi'));
    if (!targets.length) return;
    fireCooldown = 1;
    targets.forEach(t => {
      const p = enemyPos(t);
      G.turretA = Math.atan2(p.y - CY, p.x - CX);
      let dmg = stat('dmg');
      const opts = {};
      if (Math.random() < stat('crit')) { dmg *= stat('critMult'); opts.crit = true; }
      G.projectiles.push({
        x: CX + Math.cos(G.turretA) * (BASTION_R + 6),
        y: CY + Math.sin(G.turretA) * (BASTION_R + 6),
        targetId: t.id, spd: 540, dmg, opts,
        trail: [], splash: stat('splash'),
      });
    });
    AudioSys.shoot();
  }

  function updateProjectile(pr, dt) {
    let target = null;
    for (const e of G.enemies) if (e.id === pr.targetId && !e.dead) { target = e; break; }
    if (!target) { pr.dead = true; return; }
    const tp = enemyPos(target);
    const d = Math.hypot(tp.x - pr.x, tp.y - pr.y);
    const step = pr.spd * dt;
    pr.trail.push({ x: pr.x, y: pr.y });
    if (pr.trail.length > 6) pr.trail.shift();
    if (d <= step + target.def.r) {
      pr.dead = true;
      if (pr.splash > 0) {
        AudioSys.boom();
        addParticles(tp.x, tp.y, '#ff9d66', 12);
        G.enemies.forEach(e => {
          if (e.dead) return;
          const ep = enemyPos(e);
          if (Math.hypot(tp.x - ep.x, tp.y - ep.y) <= pr.splash + e.def.r) damageEnemy(e, pr.dmg, pr.opts);
        });
      } else {
        damageEnemy(target, pr.dmg, pr.opts);
      }
      return;
    }
    pr.x += (tp.x - pr.x) / d * step;
    pr.y += (tp.y - pr.y) / d * step;
  }

  // ================================================================
  // Effects
  // ================================================================
  function addFloat(p, text, color) {
    G.floats.push({ x: p.x, y: p.y - 14, text, color, ttl: 1.1 });
  }
  function addParticles(x, y, color, n) {
    for (let i = 0; i < n; i++) {
      const a = Math.random() * Math.PI * 2, v = 40 + Math.random() * 110;
      G.particles.push({ x, y, vx: Math.cos(a) * v, vy: Math.sin(a) * v, color, ttl: 0.35 + Math.random() * 0.35, size: 2 + Math.random() * 2 });
    }
  }

  // ================================================================
  // Run lifecycle
  // ================================================================
  function newRun() {
    G.state = 'run';
    G.wave = 0; G.eraIdx = 0; G.trialsPassed = 0;
    G.coins = 120 + 50 * wLv('wStart');
    G.score = 0; G.kills = 0; G.wisdomGain = 0;
    G.levels = {};
    G.hpMax = stat('hpMax'); G.hp = G.hpMax;
    G.enemies = []; G.projectiles = []; G.particles = []; G.floats = [];
    G.waveActive = false; G.interTimer = 1.0; G.awaitTrial = false;
    G.overTimer = 0; G.overActive = 0;
    G.doubler = false; G.revived = false;
    G.paused = false;
    fireCooldown = 0;
    hud.pauseBtn.textContent = '⏸';
    applyEra(0);
    hideModal();
    updateHud(true);
  }

  function applyEra(idx) {
    G.eraIdx = idx;
    drawBackground();
    buildUpgradePanel();
  }

  function onDeath() {
    G.hp = 0;
    if (G.state !== 'run') return;
    G.state = 'gameover';
    showGameOver();
  }

  function reviveWithGems() {
    if (META.gems < GEM_COST_REVIVE || G.revived) return;
    META.gems -= GEM_COST_REVIVE;
    G.revived = true;
    saveMeta();
    AudioSys.gem();
    G.hp = G.hpMax;
    G.enemies = []; G.projectiles = [];
    G.state = 'run';
    G.waveActive = false; G.interTimer = 2.0; G.spawnLeft = 0;
    hideModal();
    updateHud(true);
  }

  // ================================================================
  // Math Trial flow
  // ================================================================
  const Trial = { questions: [], idx: 0, correct: 0, answered: false };

  function openTrial() {
    G.state = 'trial';
    Trial.questions = [];
    const gen = QUESTION_GENS[G.trialsPassed];
    for (let i = 0; i < TRIAL_QUESTIONS; i++) Trial.questions.push(gen());
    Trial.idx = 0; Trial.correct = 0; Trial.answered = false;
    const m = ERAS[G.trialsPassed].mentor;
    showModal(
      '<div class="mb-mentor"><span class="mb-mentor-emoji">' + m.emoji + '</span>' +
      '<div><h3>Math Trial: ' + esc(ERAS[G.trialsPassed].name) + '</h3>' +
      '<p class="mb-mentor-name">' + esc(m.name) + '</p></div></div>' +
      '<p class="mb-modal-text">' + esc(m.trial) + '</p>' +
      '<p class="mb-modal-sub">Answer ' + TRIAL_PASS + ' of ' + TRIAL_QUESTIONS + ' correctly to advance to the next age. Waves are held while you think. No timer, no pressure.</p>' +
      '<button class="mb-btn mb-btn-primary" data-act="trial-start">Begin the trial</button>'
    );
  }

  function showTrialQuestion() {
    const q = Trial.questions[Trial.idx];
    Trial.answered = false;
    let html = '<p class="mb-trial-progress">Question ' + (Trial.idx + 1) + ' of ' + TRIAL_QUESTIONS +
      ' · ' + Trial.correct + ' correct</p>' +
      '<p class="mb-trial-q">' + esc(q.q) + '</p><div class="mb-trial-opts">';
    q.opts.forEach((opt, i) => {
      html += '<button class="mb-trial-opt" data-act="trial-answer" data-i="' + i + '">' + esc(opt) + '</button>';
    });
    html += '</div><div class="mb-trial-explain" hidden></div>';
    showModal(html);
  }

  function answerTrial(i) {
    if (Trial.answered) return;
    Trial.answered = true;
    const q = Trial.questions[Trial.idx];
    const good = i === q.answer;
    if (good) { Trial.correct++; AudioSys.right(); } else AudioSys.wrong();
    overlay.querySelectorAll('.mb-trial-opt').forEach((btn, j) => {
      btn.disabled = true;
      if (j === q.answer) btn.classList.add('is-right');
      else if (j === i) btn.classList.add('is-wrong');
    });
    const ex = overlay.querySelector('.mb-trial-explain');
    ex.hidden = false;
    ex.innerHTML = '<p>' + (good ? '✔ Correct. ' : '✘ Not quite. ') + esc(q.explain) + '</p>' +
      '<button class="mb-btn mb-btn-primary" data-act="trial-next">' +
      (Trial.idx + 1 < TRIAL_QUESTIONS ? 'Next question' : 'See the result') + '</button>';
  }

  function nextTrialStep() {
    Trial.idx++;
    if (Trial.idx < TRIAL_QUESTIONS) { showTrialQuestion(); return; }
    if (Trial.correct >= TRIAL_PASS) passTrial(); else failTrial();
  }

  function passTrial() {
    const clearedEra = ERAS[G.trialsPassed];
    G.trialsPassed++;
    const newEra = ERAS[Math.min(G.trialsPassed, ERAS.length - 1)];
    const coinReward = Math.round(200 * coinScale());
    G.coins += coinReward;
    G.score += 800;
    let gemLine = '';
    if (!META.erasCleared.includes(clearedEra.id)) {
      META.erasCleared.push(clearedEra.id);
      META.gems += GEMS_ERA_CLEAR;
      gemLine = '<p class="mb-reward-gems">💎 +' + GEMS_ERA_CLEAR + ' gems, first time clearing this age!</p>';
      AudioSys.gem();
    }
    saveMeta();
    AudioSys.fanfare();
    showModal(
      '<div class="mb-mentor"><span class="mb-mentor-emoji">' + newEra.mentor.emoji + '</span>' +
      '<div><h3>' + esc(newEra.name) + '</h3><p class="mb-mentor-name">' + esc(newEra.years) + ', ' + esc(newEra.mentor.name) + '</p></div></div>' +
      '<p class="mb-modal-text">' + esc(newEra.mentor.intro) + '</p>' +
      '<p class="mb-reward">🏆 Trial passed (' + Trial.correct + '/' + TRIAL_QUESTIONS + ') · +' + coinReward + ' coins · new discoveries unlocked in the shop</p>' +
      gemLine +
      '<p class="mb-modal-sub">' + esc(newEra.mentor.blurb) + '</p>' +
      '<button class="mb-btn mb-btn-primary" data-act="trial-done">Enter the new age</button>'
    );
  }

  function failTrial() {
    const m = ERAS[G.trialsPassed].mentor;
    showModal(
      '<div class="mb-mentor"><span class="mb-mentor-emoji">' + m.emoji + '</span>' +
      '<div><h3>Not yet, study and retry</h3><p class="mb-mentor-name">' + esc(m.name) + '</p></div></div>' +
      '<p class="mb-modal-text">You answered ' + Trial.correct + ' of ' + TRIAL_QUESTIONS + '. ' +
      'History waited for these ideas too. Read the explanations, take a breath, and try a fresh set of questions. There is no penalty.</p>' +
      '<p class="mb-modal-sub">' + esc(m.blurb) + '</p>' +
      '<button class="mb-btn mb-btn-primary" data-act="trial-retry">Try a new set</button>'
    );
  }

  function completeTrial() {
    G.awaitTrial = false;
    G.state = 'run';
    applyEra(Math.min(eraForWave(G.wave), ERAS.length - 1));
    G.interTimer = 2.0;
    hideModal();
    updateHud(true);
  }

  // ================================================================
  // Rendering
  // ================================================================
  const canvas = root.querySelector('canvas');
  const dpr = Math.min(2, window.devicePixelRatio || 1);
  canvas.width = W * dpr; canvas.height = H * dpr;
  const ctx = canvas.getContext('2d');
  ctx.scale(dpr, dpr);

  const bgCanvas = document.createElement('canvas');
  bgCanvas.width = W * dpr; bgCanvas.height = H * dpr;
  const STARS = [];
  for (let i = 0; i < 70; i++) {
    STARS.push({ x: Math.random() * W, y: Math.random() * H, r: 0.6 + Math.random() * 1.6, tw: Math.random() * Math.PI * 2 });
  }

  function drawBackground() {
    const c = bgCanvas.getContext('2d');
    c.setTransform(dpr, 0, 0, dpr, 0, 0);
    const pal = era().pal;
    const grad = c.createRadialGradient(CX, CY, 60, CX, CY, Math.max(W, H) * 0.72);
    grad.addColorStop(0, pal.sky1);
    grad.addColorStop(1, pal.sky0);
    c.fillStyle = grad;
    c.fillRect(0, 0, W, H);

    // Concentric range rings
    c.strokeStyle = 'rgba(255,255,255,0.05)';
    c.lineWidth = 1;
    for (let r = 90; r < 480; r += 65) {
      c.beginPath(); c.arc(CX, CY, r, 0, Math.PI * 2); c.stroke();
    }

    // Era glyph decorations scattered around the arena
    c.save();
    c.globalAlpha = 0.28;
    c.fillStyle = pal.deco;
    c.font = '16px "Fraunces", serif';
    c.textAlign = 'center';
    const glyphs = {
      prehistory: ['𝍫', '𝍩', '𝍪'], egypt: ['△', '𓂀', '𐤎'], greece: ['△', '□', '⬠'],
      goldenage: ['٠', '٥', '✶'], revolution: ['∫', 'Δ', '(x,y)'], frontier: ['∞', 'ℵ', 'i'],
    }[era().id] || ['·'];
    for (let i = 0; i < 22; i++) {
      const a = (i / 22) * Math.PI * 2 + i * 0.7;
      const rr = 250 + (i * 53 % 130);
      const x = CX + Math.cos(a) * rr, y = CY + Math.sin(a) * rr * 0.72;
      if (x < 12 || x > W - 12 || y < 16 || y > H - 8) continue;
      c.save(); c.translate(x, y); c.rotate((i * 37 % 60 - 30) * 0.02);
      c.fillText(glyphs[i % glyphs.length], 0, 0);
      c.restore();
    }
    c.restore();

    // Vignette
    const vg = c.createRadialGradient(CX, CY, H * 0.45, CX, CY, H * 0.95);
    vg.addColorStop(0, 'rgba(0,0,0,0)');
    vg.addColorStop(1, 'rgba(0,0,0,0.5)');
    c.fillStyle = vg;
    c.fillRect(0, 0, W, H);
  }

  function draw() {
    ctx.save();
    if (G.shake > 0.2) {
      ctx.translate((Math.random() - 0.5) * G.shake, (Math.random() - 0.5) * G.shake);
    }
    ctx.drawImage(bgCanvas, 0, 0, W, H);
    const pal = era().pal;

    // Twinkling stars
    STARS.forEach(s => {
      ctx.globalAlpha = 0.25 + 0.45 * (0.5 + 0.5 * Math.sin(G.time * 1.4 + s.tw));
      ctx.fillStyle = pal.star;
      ctx.beginPath(); ctx.arc(s.x, s.y, s.r, 0, Math.PI * 2); ctx.fill();
    });
    ctx.globalAlpha = 1;

    drawFields();
    drawBastion(pal);
    G.enemies.forEach(drawEnemy);
    drawProjectiles(pal);

    // Particles
    G.particles.forEach(p => {
      ctx.globalAlpha = Math.max(0, p.ttl / 0.6);
      ctx.fillStyle = p.color;
      ctx.fillRect(p.x - p.size / 2, p.y - p.size / 2, p.size, p.size);
    });
    ctx.globalAlpha = 1;

    // Floating text
    ctx.font = 'bold 13px "Source Sans 3", sans-serif';
    ctx.textAlign = 'center';
    G.floats.forEach(f => {
      ctx.globalAlpha = Math.min(1, Math.max(0, f.ttl));
      ctx.fillStyle = f.color;
      ctx.fillText(f.text, f.x, f.y - (1.1 - f.ttl) * 26);
    });
    ctx.globalAlpha = 1;
    ctx.restore();
  }

  function drawFields() {
    // Range circle
    ctx.save();
    ctx.strokeStyle = 'rgba(255,255,255,0.14)';
    ctx.setLineDash([5, 7]);
    ctx.lineWidth = 1.4;
    ctx.beginPath(); ctx.arc(CX, CY, stat('range'), 0, Math.PI * 2); ctx.stroke();
    ctx.setLineDash([]);
    // Fraction field wash
    if (lv('slow')) {
      ctx.globalAlpha = 0.05 + 0.01 * Math.sin(G.time * 2);
      ctx.fillStyle = '#4da3c0';
      ctx.beginPath(); ctx.arc(CX, CY, stat('range'), 0, Math.PI * 2); ctx.fill();
      ctx.globalAlpha = 1;
    }
    // Zero well
    if (lv('well')) {
      const wr = BASTION_R + 110;
      const g = ctx.createRadialGradient(CX, CY, BASTION_R, CX, CY, wr);
      g.addColorStop(0, 'rgba(60,90,200,0.16)');
      g.addColorStop(1, 'rgba(60,90,200,0)');
      ctx.fillStyle = g;
      ctx.beginPath(); ctx.arc(CX, CY, wr, 0, Math.PI * 2); ctx.fill();
    }
    ctx.restore();
  }

  function drawBastion(pal) {
    ctx.save();
    ctx.translate(CX, CY);
    // Glow
    ctx.shadowColor = pal.glow;
    ctx.shadowBlur = G.overActive > 0 ? 34 : 20;
    ctx.fillStyle = '#0e1420';
    ctx.strokeStyle = pal.glow;
    ctx.lineWidth = 2.5;
    ctx.beginPath(); ctx.arc(0, 0, BASTION_R, 0, Math.PI * 2); ctx.fill(); ctx.stroke();
    ctx.shadowBlur = 0;
    // Rotating rune ring
    ctx.save();
    ctx.rotate(G.time * 0.25);
    ctx.fillStyle = 'rgba(255,255,255,0.55)';
    ctx.font = '11px "Fraunces", serif';
    ctx.textAlign = 'center'; ctx.textBaseline = 'middle';
    const runes = ['𝍫', '½', 'ℙ', '0', 'dx', '×', '𝑥', '△'];
    runes.forEach((r, i) => {
      const a = (i / runes.length) * Math.PI * 2;
      ctx.save();
      ctx.translate(Math.cos(a) * (BASTION_R - 11), Math.sin(a) * (BASTION_R - 11));
      ctx.rotate(a + Math.PI / 2);
      ctx.fillText(r, 0, 0);
      ctx.restore();
    });
    ctx.restore();
    // Turret
    ctx.save();
    ctx.rotate(G.turretA);
    ctx.fillStyle = pal.glow;
    ctx.shadowColor = pal.glow; ctx.shadowBlur = 10;
    ctx.fillRect(6, -4.5, BASTION_R - 2, 9);
    ctx.beginPath(); ctx.arc(0, 0, 12, 0, Math.PI * 2); ctx.fill();
    ctx.restore();
    // Core sigil
    ctx.fillStyle = '#0e1420';
    ctx.beginPath(); ctx.arc(0, 0, 9, 0, Math.PI * 2); ctx.fill();
    ctx.fillStyle = '#fff';
    ctx.font = 'bold 11px "Fraunces", serif';
    ctx.textAlign = 'center'; ctx.textBaseline = 'middle';
    ctx.fillText('∑', 0, 0.5);
    // HP ring
    const frac = G.hpMax ? Math.max(0, G.hp / G.hpMax) : 1;
    ctx.lineWidth = 5;
    ctx.strokeStyle = 'rgba(255,255,255,0.12)';
    ctx.beginPath(); ctx.arc(0, 0, BASTION_R + 8, 0, Math.PI * 2); ctx.stroke();
    ctx.strokeStyle = frac > 0.5 ? '#7de8a0' : frac > 0.25 ? '#ffd23f' : '#ff7777';
    ctx.beginPath(); ctx.arc(0, 0, BASTION_R + 8, -Math.PI / 2, -Math.PI / 2 + frac * Math.PI * 2); ctx.stroke();
    ctx.restore();
  }

  function drawEnemy(e) {
    const p = enemyPos(e);
    const def = e.def;
    const r = def.r;
    ctx.save();
    ctx.translate(p.x, p.y);
    if (def.ghost) ctx.globalAlpha = 0.7;
    ctx.shadowColor = def.color;
    ctx.shadowBlur = def.boss ? 22 : 9;
    ctx.fillStyle = e.flash > 0 ? '#ffffff' : def.color;
    ctx.strokeStyle = def.prime ? '#e8ccff' : 'rgba(0,0,0,0.4)';
    ctx.lineWidth = def.prime ? 2.2 : 1.4;
    ctx.beginPath();
    const rot = e.angle + G.time * (def.shape === 'spark' ? 3 : 0.6);
    if (def.shape === 'tri') {
      for (let i = 0; i < 3; i++) {
        const a = rot + (i / 3) * Math.PI * 2;
        i ? ctx.lineTo(Math.cos(a) * r, Math.sin(a) * r) : ctx.moveTo(Math.cos(a) * r, Math.sin(a) * r);
      }
      ctx.closePath();
    } else if (def.shape === 'hex') {
      for (let i = 0; i < 6; i++) {
        const a = rot + (i / 6) * Math.PI * 2;
        i ? ctx.lineTo(Math.cos(a) * r, Math.sin(a) * r) : ctx.moveTo(Math.cos(a) * r, Math.sin(a) * r);
      }
      ctx.closePath();
    } else if (def.shape === 'spark') {
      for (let i = 0; i < 8; i++) {
        const a = rot + (i / 8) * Math.PI * 2;
        const rr = i % 2 ? r * 0.55 : r * 1.15;
        i ? ctx.lineTo(Math.cos(a) * rr, Math.sin(a) * rr) : ctx.moveTo(Math.cos(a) * rr, Math.sin(a) * rr);
      }
      ctx.closePath();
    } else if (def.shape === 'ghost') {
      ctx.arc(0, 0, r, Math.PI, 0);
      ctx.lineTo(r, r * 0.8);
      for (let i = 0; i < 3; i++) {
        ctx.quadraticCurveTo(r - (i * 2 + 0.5) * r / 3, r * (0.55 + 0.18 * Math.sin(e.wobA * 2 + i)), r - (i + 1) * (2 * r / 3), r * 0.8);
      }
      ctx.closePath();
    } else if (def.shape === 'boss') {
      for (let i = 0; i < 12; i++) {
        const a = rot * 0.4 + (i / 12) * Math.PI * 2;
        const rr = r * (i % 2 ? 0.85 : 1.18);
        i ? ctx.lineTo(Math.cos(a) * rr, Math.sin(a) * rr) : ctx.moveTo(Math.cos(a) * rr, Math.sin(a) * rr);
      }
      ctx.closePath();
    } else {
      const squish = 1 + 0.06 * Math.sin(e.wobA * 2);
      ctx.ellipse(0, 0, r * squish, r / squish, 0, 0, Math.PI * 2);
    }
    ctx.fill();
    ctx.shadowBlur = 0;
    ctx.stroke();

    // Number / label: enemies wear their mathematics.
    const label = e.label !== null ? e.label : (e.num !== null ? String(e.num) : '');
    if (label) {
      ctx.fillStyle = '#fff';
      ctx.font = 'bold ' + Math.max(8, r * 0.7) + 'px "JetBrains Mono", monospace';
      ctx.textAlign = 'center'; ctx.textBaseline = 'middle';
      ctx.fillText(label, 0, 0);
    }
    // HP bar (only when damaged)
    if (e.hp < e.maxHp) {
      const w = r * 2;
      ctx.fillStyle = 'rgba(0,0,0,0.55)';
      ctx.fillRect(-w / 2, -r - 8, w, 3.5);
      ctx.fillStyle = e.hp / e.maxHp > 0.4 ? '#7de8a0' : '#ff9d66';
      ctx.fillRect(-w / 2, -r - 8, w * Math.max(0, e.hp / e.maxHp), 3.5);
    }
    ctx.restore();
  }

  function drawProjectiles(pal) {
    G.projectiles.forEach(pr => {
      ctx.save();
      for (let i = 0; i < pr.trail.length; i++) {
        const t = pr.trail[i];
        ctx.globalAlpha = (i + 1) / pr.trail.length * 0.4;
        ctx.fillStyle = pal.glow;
        ctx.beginPath(); ctx.arc(t.x, t.y, 2.4, 0, Math.PI * 2); ctx.fill();
      }
      ctx.globalAlpha = 1;
      ctx.shadowColor = pal.glow; ctx.shadowBlur = 8;
      ctx.fillStyle = '#fff';
      ctx.beginPath(); ctx.arc(pr.x, pr.y, pr.splash ? 4.5 : 3.2, 0, Math.PI * 2); ctx.fill();
      ctx.restore();
    });
  }

  // ================================================================
  // Main loop
  // ================================================================
  let lastTs = null;
  function frame(ts) {
    requestAnimationFrame(frame);
    if (lastTs === null) lastTs = ts;
    let dt = Math.min(0.05, (ts - lastTs) / 1000);
    lastTs = ts;

    if (G.state === 'run' && !G.paused) {
      dt *= G.speed;
      G.time += dt;
      G.shake = Math.max(0, G.shake - dt * 30);
      G.hp = Math.min(G.hpMax, G.hp + stat('regen') * dt);
      updateSpawning(dt);
      updateCombat(dt);
      G.enemies.forEach(e => { if (!e.dead) updateEnemy(e, dt); });
      G.enemies = G.enemies.filter(e => !e.dead);
      G.projectiles.forEach(p => updateProjectile(p, dt));
      G.projectiles = G.projectiles.filter(p => !p.dead);
    } else {
      G.time += dt * 0.3; // idle shimmer on menus
    }
    G.floats.forEach(f => { f.ttl -= dt; });
    G.floats = G.floats.filter(f => f.ttl > 0);
    G.particles.forEach(p => { p.ttl -= dt; p.x += p.vx * dt; p.y += p.vy * dt; p.vy += 150 * dt; });
    G.particles = G.particles.filter(p => p.ttl > 0);

    draw();
    updateHud(false);
  }

  // ================================================================
  // DOM: HUD, upgrade panel, modals
  // ================================================================
  const $ = sel => root.querySelector(sel);
  const overlay = $('.mb-overlay');
  const hud = {
    era: $('.mb-era-name'), wave: $('.mb-wave'), hpbar: $('.mb-hpbar-fill'), hptext: $('.mb-hptext'),
    coins: $('.mb-coins'), gems: $('.mb-gems'), score: $('.mb-score'),
    speedBtn: $('.mb-speed-btn'), pauseBtn: $('.mb-pause-btn'), muteBtn: $('.mb-mute-btn'),
    tabs: $('.mb-tabs'), ups: $('.mb-upgrades'),
  };

  let hudTimer = 0, upgradesDirty = true, activeTab = 'attack';
  function markUpgradesDirty() { upgradesDirty = true; }

  function updateHud(force) {
    hudTimer -= 1;
    if (!force && hudTimer > 0) return;
    hudTimer = 6; // ~10 Hz at 60 fps
    hud.era.textContent = era().name;
    hud.wave.textContent = G.state === 'menu' ? '-' : 'Wave ' + (G.awaitTrial ? G.wave : G.wave + 1);
    const frac = G.hpMax ? Math.max(0, G.hp / G.hpMax) : 1;
    hud.hpbar.style.width = (frac * 100).toFixed(1) + '%';
    hud.hpbar.className = 'mb-hpbar-fill' + (frac < 0.25 ? ' is-low' : frac < 0.5 ? ' is-mid' : '');
    hud.hptext.textContent = Math.ceil(G.hp) + ' / ' + Math.round(G.hpMax);
    hud.coins.textContent = fmt(G.coins);
    hud.gems.textContent = fmt(META.gems);
    hud.score.textContent = fmt(G.score);
    if (upgradesDirty) refreshUpgradeButtons();
  }

  function visibleUpgrades(tab) {
    return UPGRADES.filter(u => u.tab === tab && u.era <= G.trialsPassed);
  }

  function buildUpgradePanel() {
    hud.tabs.innerHTML = TABS.map(t =>
      '<button class="mb-tab' + (t.id === activeTab ? ' is-active' : '') + '" data-tab="' + t.id + '">' + t.label + '</button>'
    ).join('');
    hud.ups.innerHTML = visibleUpgrades(activeTab).map(u =>
      '<button class="mb-upg" data-upg="' + u.id + '" title="' + esc(u.note) + '">' +
      '<span class="mb-upg-icon">' + u.icon + '</span>' +
      '<span class="mb-upg-main"><span class="mb-upg-name">' + esc(u.name) +
      ' <em class="mb-upg-lv"></em></span>' +
      '<span class="mb-upg-desc"></span></span>' +
      '<span class="mb-upg-cost"></span></button>'
    ).join('') || '<p class="mb-upg-empty">New discoveries unlock when you pass this age’s Math Trial.</p>';
    upgradesDirty = true;
  }

  function refreshUpgradeButtons() {
    upgradesDirty = false;
    visibleUpgrades(activeTab).forEach(u => {
      const btn = hud.ups.querySelector('[data-upg="' + u.id + '"]');
      if (!btn) return;
      const level = lv(u.id), maxed = level >= u.max;
      const cost = upgCost(u);
      btn.querySelector('.mb-upg-lv').textContent = 'lv ' + level + (maxed ? ' MAX' : '');
      btn.querySelector('.mb-upg-desc').textContent = u.desc(level);
      btn.querySelector('.mb-upg-cost').textContent = maxed ? '-' : fmt(cost) + ' 🪙';
      btn.disabled = maxed || G.coins < cost || G.state !== 'run';
      btn.classList.toggle('is-affordable', !maxed && G.coins >= cost && G.state === 'run');
    });
  }

  function buyUpgrade(id) {
    const u = UPGRADES.find(x => x.id === id);
    if (!u || G.state !== 'run') return;
    const cost = upgCost(u);
    if (lv(id) >= u.max || G.coins < cost) return;
    G.coins -= cost;
    G.levels[id] = lv(id) + 1;
    const prevMax = G.hpMax;
    G.hpMax = stat('hpMax');
    if (G.hpMax > prevMax) G.hp += G.hpMax - prevMax;
    AudioSys.buy();
    markUpgradesDirty();
    updateHud(true);
  }

  // ---------------- Modals ----------------
  function showModal(html, wide) {
    overlay.innerHTML = '<div class="mb-modal' + (wide ? ' mb-modal-wide' : '') + '">' + html + '</div>';
    overlay.classList.add('is-open');
  }
  function hideModal() {
    overlay.classList.remove('is-open');
    overlay.innerHTML = '';
  }
  function esc(s) {
    return String(s).replace(/[&<>"']/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
  }

  function showMenu() {
    G.state = 'menu';
    showModal(
      '<h2 class="mb-title">Math Bastion</h2>' +
      '<p class="mb-modal-sub mb-title-sub">An idle tower defense through the history of mathematics</p>' +
      '<p class="mb-modal-text">One bastion. Endless waves from every direction. Upgrade in real time, and pass each age’s <strong>Math Trial</strong>, set by the people who actually discovered the ideas, to reach the next era of history.</p>' +
      (META.bestWave ? '<p class="mb-reward">Best run: wave ' + META.bestWave + ' · Wisdom: ' + fmt(META.wisdom) + ' · 💎 ' + fmt(META.gems) + '</p>' : '') +
      '<div class="mb-btn-row">' +
      '<button class="mb-btn mb-btn-primary" data-act="start">▶ Begin the campaign</button>' +
      '<button class="mb-btn" data-act="workshop">🏗 Workshop</button>' +
      '<button class="mb-btn" data-act="store">💎 Gem Store</button>' +
      '<button class="mb-btn" data-act="codex">📖 Codex</button>' +
      '<button class="mb-btn" data-act="lb">🏆 Leaderboard</button>' +
      '</div>'
    );
  }

  function showGameOver() {
    if (!G.wisdomGain) {
      G.wisdomGain = Math.max(1, Math.floor(G.wave * 1.2 + G.trialsPassed * 8));
      META.wisdom += G.wisdomGain;
      saveMeta();
    }
    const reviveOk = !G.revived && META.gems >= GEM_COST_REVIVE;
    showModal(
      '<h3>The bastion has fallen</h3>' +
      '<p class="mb-modal-text">You held for <strong>' + G.wave + ' waves</strong> and reached <strong>' +
      esc(era().name) + '</strong>. Score: <strong>' + fmt(G.score) + '</strong> · Kills: ' + fmt(G.kills) + '</p>' +
      '<p class="mb-reward">🧠 +' + G.wisdomGain + ' Wisdom for the Workshop</p>' +
      '<div class="mb-btn-row">' +
      (reviveOk ? '<button class="mb-btn mb-btn-gem" data-act="revive">💎 Second Wind: revive (' + GEM_COST_REVIVE + ' gems)</button>' : '') +
      '<button class="mb-btn mb-btn-primary" data-act="start">↻ New run</button>' +
      '<button class="mb-btn" data-act="workshop">🏗 Workshop</button>' +
      '</div>' +
      '<div class="mb-submit"><input class="mb-name" maxlength="20" placeholder="Name for the leaderboard">' +
      '<button class="mb-btn" data-act="submit-score">Submit score</button><span class="mb-submit-msg"></span></div>'
    );
  }

  function showWorkshop() {
    const back = G.state === 'gameover' ? 'gameover' : 'menu';
    let html = '<h3>🏗 The Workshop</h3>' +
      '<p class="mb-modal-sub">Permanent upgrades, paid with Wisdom earned from every run. Wisdom: <strong>' + fmt(META.wisdom) + '</strong></p>' +
      '<div class="mb-work-list">';
    WORKSHOP.forEach(w => {
      const level = wLv(w.id), cost = workCost(w), maxed = level >= w.max;
      html += '<button class="mb-upg" data-work="' + w.id + '" ' + (maxed || META.wisdom < cost ? 'disabled' : '') + '>' +
        '<span class="mb-upg-main"><span class="mb-upg-name">' + esc(w.name) + ' <em class="mb-upg-lv">lv ' + level + (maxed ? ' MAX' : '') + '</em></span>' +
        '<span class="mb-upg-desc">' + esc(w.desc) + '</span></span>' +
        '<span class="mb-upg-cost">' + (maxed ? '-' : fmt(cost) + ' 🧠') + '</span></button>';
    });
    html += '</div><button class="mb-btn" data-act="' + back + '">← Back</button>';
    showModal(html, true);
  }

  function showCodex() {
    const back = G.state === 'run' || G.state === 'trial' ? 'close' : 'menu';
    let html = '<h3>📖 Discovery Codex</h3><p class="mb-modal-sub">The real history behind each age.</p><div class="mb-codex">';
    ERAS.forEach((e, i) => {
      const open = META.erasCleared.includes(e.id) || i <= G.trialsPassed;
      html += '<div class="mb-codex-item' + (open ? '' : ' is-locked') + '">' +
        '<h4>' + e.mentor.emoji + ' ' + esc(e.name) + ' <span>' + esc(e.years) + '</span></h4>' +
        (open ? '<p><strong>' + esc(e.mentor.discovery) + '.</strong> ' + esc(e.mentor.blurb) + '</p>'
              : '<p>Locked. Reach this age to read its story.</p>') +
        '</div>';
    });
    html += '</div><button class="mb-btn" data-act="' + back + '">← Back</button>';
    showModal(html, true);
  }

  // ---------------- Store (micropayment scaffold) ----------------
  let storeCache = null;
  function showStore() {
    const back = G.state === 'run' ? 'close' : 'menu';
    let html = '<h3>💎 Gem Store</h3>' +
      '<p class="mb-modal-sub">Gems power optional extras: Second Wind revives (' + GEM_COST_REVIVE + ') and a run-long Coin Doubler (' + GEM_COST_DOUBLER + '). You hold <strong>' + fmt(META.gems) + '</strong> gems.</p>';
    if (G.state === 'run') {
      html += '<div class="mb-btn-row">' +
        '<button class="mb-btn mb-btn-gem" data-act="doubler" ' + (G.doubler || META.gems < GEM_COST_DOUBLER ? 'disabled' : '') + '>' +
        (G.doubler ? '✓ Coin Doubler active' : '2× coins this run (' + GEM_COST_DOUBLER + ' 💎)') + '</button></div>';
    }
    html += '<div class="mb-store-list">Loading gem packs…</div>' +
      '<p class="mb-store-note"></p>' +
      '<button class="mb-btn" data-act="' + back + '">← Back</button>';
    showModal(html, true);
    const list = overlay.querySelector('.mb-store-list');
    const note = overlay.querySelector('.mb-store-note');
    const render = data => {
      storeCache = data;
      list.innerHTML = data.products.map(p =>
        '<button class="mb-upg mb-pack" data-sku="' + esc(p.sku) + '">' +
        '<span class="mb-upg-icon">💎</span>' +
        '<span class="mb-upg-main"><span class="mb-upg-name">' + esc(p.name) + '</span>' +
        '<span class="mb-upg-desc">' + p.gems + (p.bonus_gems ? ' +' + p.bonus_gems + ' bonus' : '') + ' gems · ' + esc(p.description) + '</span></span>' +
        '<span class="mb-upg-cost">$' + (p.price_cents / 100).toFixed(2) + '</span></button>'
      ).join('') || '<p class="mb-upg-empty">No gem packs configured.</p>';
      note.textContent = data.payments_enabled
        ? 'Purchases are processed securely by our payment provider.'
        : 'Checkout is coming soon. Purchases are not yet enabled, and no card details are collected.';
    };
    if (storeCache) render(storeCache);
    else if (URLS.store) {
      fetch(URLS.store).then(r => r.json()).then(render)
        .catch(() => { list.innerHTML = '<p class="mb-upg-empty">Store unavailable right now.</p>'; });
    }
  }

  function buyPack(sku) {
    const note = overlay.querySelector('.mb-store-note');
    if (!URLS.purchase || !note) return;
    note.textContent = 'Contacting the store…';
    api(URLS.purchase, { device_key: META.deviceKey, sku })
      .then(res => {
        if (res.ok && res.checkout) {
          // TODO(payments): redirect to res.checkout when a provider is live.
          window.location = res.checkout;
        } else {
          note.textContent = res.message || 'Checkout is not available yet. Your interest was recorded. Payments arrive with the app release!';
        }
      })
      .catch(() => { note.textContent = 'Could not reach the store. Try again later.'; });
  }

  function buyDoubler() {
    if (G.doubler || META.gems < GEM_COST_DOUBLER) return;
    META.gems -= GEM_COST_DOUBLER;
    G.doubler = true;
    saveMeta();
    AudioSys.gem();
    showStore();
    updateHud(true);
  }

  // ---------------- Leaderboard ----------------
  function showLeaderboard() {
    const back = G.state === 'gameover' ? 'gameover' : 'menu';
    showModal('<h3>🏆 Leaderboard</h3><div class="mb-lb">Loading…</div><button class="mb-btn" data-act="' + back + '">← Back</button>', true);
    fetch(URLS.leaderboard).then(r => r.json()).then(data => {
      const el = overlay.querySelector('.mb-lb');
      if (!el) return;
      el.innerHTML = data.scores.length
        ? '<ol>' + data.scores.map(s =>
            '<li><strong>' + esc(s.name) + '</strong>: ' + fmt(s.score) + ' pts · wave ' + s.waves + ' · ' + esc(s.era) + '</li>'
          ).join('') + '</ol>'
        : '<p>No scores yet. Be the first!</p>';
    }).catch(() => {});
  }

  function submitScore() {
    const input = overlay.querySelector('.mb-name');
    const msg = overlay.querySelector('.mb-submit-msg');
    const name = (input && input.value.trim()) || 'Anonymous';
    msg.textContent = 'Submitting…';
    api(URLS.submit, {
      name, score: G.score, waves: G.wave, era: era().name, victory: G.trialsPassed >= QUESTION_GENS.length,
    }).then(res => { msg.textContent = res.ok ? '✔ Submitted!' : 'Could not submit.'; })
      .catch(() => { msg.textContent = 'Could not submit.'; });
  }

  // ================================================================
  // Events
  // ================================================================
  root.addEventListener('click', ev => {
    const tabBtn = ev.target.closest('[data-tab]');
    if (tabBtn) { activeTab = tabBtn.dataset.tab; buildUpgradePanel(); refreshUpgradeButtons(); return; }
    const upgBtn = ev.target.closest('[data-upg]');
    if (upgBtn) { buyUpgrade(upgBtn.dataset.upg); return; }
    const workBtn = ev.target.closest('[data-work]');
    if (workBtn) {
      const w = WORKSHOP.find(x => x.id === workBtn.dataset.work);
      if (w && wLv(w.id) < w.max && META.wisdom >= workCost(w)) {
        META.wisdom -= workCost(w);
        META.workshop[w.id] = wLv(w.id) + 1;
        saveMeta(); AudioSys.buy(); showWorkshop();
      }
      return;
    }
    const packBtn = ev.target.closest('[data-sku]');
    if (packBtn) { buyPack(packBtn.dataset.sku); return; }
    const actBtn = ev.target.closest('[data-act]');
    if (!actBtn) return;
    const act = actBtn.dataset.act;
    if (act === 'start') newRun();
    else if (act === 'menu') showMenu();
    else if (act === 'close') hideModal();
    else if (act === 'gameover') showGameOver();
    else if (act === 'workshop') showWorkshop();
    else if (act === 'store') showStore();
    else if (act === 'codex') showCodex();
    else if (act === 'lb') showLeaderboard();
    else if (act === 'revive') reviveWithGems();
    else if (act === 'doubler') buyDoubler();
    else if (act === 'submit-score') submitScore();
    else if (act === 'trial-start') showTrialQuestion();
    else if (act === 'trial-answer') answerTrial(parseInt(actBtn.dataset.i, 10));
    else if (act === 'trial-next') nextTrialStep();
    else if (act === 'trial-retry') openTrial();
    else if (act === 'trial-done') completeTrial();
  });

  hud.speedBtn.addEventListener('click', () => {
    G.speed = G.speed >= 3 ? 1 : G.speed + 1;
    hud.speedBtn.textContent = '▶ ' + G.speed + '×';
  });
  hud.pauseBtn.addEventListener('click', () => {
    if (G.state !== 'run') return;
    G.paused = !G.paused;
    hud.pauseBtn.textContent = G.paused ? '▶' : '⏸';
  });
  hud.muteBtn.addEventListener('click', () => {
    hud.muteBtn.textContent = AudioSys.toggleMute() ? '🔇' : '🔊';
  });
  $('.mb-store-hud-btn').addEventListener('click', showStore);
  $('.mb-codex-hud-btn').addEventListener('click', showCodex);

  // ================================================================
  // Boot
  // ================================================================
  hud.muteBtn.textContent = AudioSys.isMuted() ? '🔇' : '🔊';
  applyEra(0);
  showMenu();
  updateHud(true);
  requestAnimationFrame(frame);
})();

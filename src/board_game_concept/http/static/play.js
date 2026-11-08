// The replay: the record of a resolved game, a turn at a time.
//
// A game is played to its end the moment the last setup is committed, by the
// controllers and nobody else, and every turn is written as it goes. This
// screen shows that record: a scrubber over every turn, play, pause, step and
// speed, the board after each turn drawn whole from the record with every
// unit moving from its old square to its new, what the turn did, what it
// would not do for this seat, and what this seat's controllers thought.
//
// Before the game is resolved there is nothing to replay. A seat that has
// committed is told whose setups are still to come, and the screen moves to
// the replay of its own accord when the last one lands.
//
// What a seat is shown of a turn is decided by the server: the board is
// everybody's once the game is over, the traces are the seat's own, and the
// observer and the administrator are given every seat's. Nothing here
// decides what to conceal, and the board of what an army knew is drawn from
// the map the server kept for it, never worked out here.

import * as api from './api.js';
import { state, set, say, loadSeat, element, button, link } from './app.js';
import { renderBoard } from './board.js';

const WAIT_BUDGET = 25;

// the speeds a replay plays at, in turns a second
const SPEEDS = [0.5, 1, 2, 4];

export function renderPlay() {
  const game = state.game;
  if (!game) return element('p', { class: 'waiting' }, 'Loading');

  const wrap = element('div', {});
  const watching = game.number === 1000 || game.number === 0;

  wrap.append(element('h1', {},
    `Game ${game.gameno} — `,
    watching ? 'watching' : `seat ${game.number}`));
  wrap.append(element('p', {}, link('← lobby', '#/')));

  if (!game.outcome) {
    // the game is not resolved: either this seat has still to commit, or
    // it has and the others have not. Either way the record is empty and
    // the screen waits, watching for the resolution
    if (game.unprocessed_moves && !state.watching) {
      state.watching = true;
      watch(game).finally(() => { state.watching = false; });
    }
    wrap.append(renderWaiting(game));
    if (game.board) wrap.append(renderSetupBoard(game));
    return wrap;
  }

  // a resolved game opens at its final turn, with the result
  const replay = state.replay;
  const turns = replay.turns || [];
  const last = turns.length ? turns[turns.length - 1] : null;
  if (replay.turn === null || replay.record === null
      || replay.record.turn !== replay.turn
      || (replay.record.known || false) !== replay.known
      || (replay.record.seat || null) !== (replay.seat || null)) {
    const wanted = replay.turn === null ? last : replay.turn;
    if (wanted !== null && !replay.loading) {
      replay.loading = true;
      showTurn(game, wanted).finally(() => { state.replay.loading = false; });
    }
    if (replay.record === null) {
      wrap.append(renderOutcome(game, null));
      wrap.append(element('p', { class: 'waiting' }, 'Reading the record'));
      return wrap;
    }
  }

  const record = replay.record;
  wrap.append(renderOutcome(game, record));
  if (!watching && isOutAt(record, game.number)) wrap.append(renderOut(game));

  wrap.append(renderPaneSwitch());
  const layout = element('div', { class: `row panes pane-${state.pane}` });
  layout.append(element('div', { class: 'grow board-pane' },
                        renderReplayBoard(game, record)));
  const side = element('div', { class: 'grow tray-pane' });
  side.append(renderTraces(game, record));
  side.append(renderForces(game, record));
  layout.append(side);
  wrap.append(layout);

  wrap.append(renderTurnReport(game, record));
  wrap.append(renderKeys(watching));
  return wrap;
}

// --- moving through the record

/**
 * Read one turn of the record and show it.
 *
 * The board the replay draws is the record's, whole; `known` asks for the
 * board as an army knew it, and `seat` says whose army when the viewer has
 * none of its own. Nothing is kept but the one turn being shown: the record
 * is the server's, and a turn is cheap to read again.
 */
export async function showTurn(game, turn) {
  const replay = state.replay;
  const turns = replay.turns || [];
  if (!turns.length) return;
  const wanted = Math.min(Math.max(turn, turns[0]), turns[turns.length - 1]);
  const seat = replay.seat || null;
  try {
    const answer = await api.readTurn(game.gameno, game.number, wanted,
                                      replay.known, seat);
    const record = answer.turn;
    record.known = Boolean(replay.known);
    record.seat = seat;
    set({ replay: { ...state.replay, turn: wanted, record },
          cursor: state.cursor });
  } catch (error) {
    say(error.message);
    set({ replay: { ...state.replay, playing: false } });
  }
}

export function stepTurn(game, by) {
  const replay = state.replay;
  if (replay.turn === null) return;
  const turns = replay.turns || [];
  const next = replay.turn + by;
  if (next < turns[0] || next > turns[turns.length - 1]) {
    if (replay.playing) set({ replay: { ...replay, playing: false } });
    return;
  }
  showTurn(game, next);
}

/**
 * Play the record on from the turn being shown, at the chosen speed, until
 * it is paused or runs out. One timer, re-armed after each turn is drawn, so
 * a slow read never piles turns up.
 */
export function play(game) {
  const replay = state.replay;
  const turns = replay.turns || [];
  const last = turns.length ? turns[turns.length - 1] : null;
  // playing from the end starts again from the beginning: a player who
  // presses play on the final turn wants to see the game, not nothing
  const from = replay.turn === last ? turns[0] : replay.turn;
  set({ replay: { ...replay, playing: true } });
  const tick = async () => {
    const now = state.replay;
    if (!now.playing || state.route.name !== 'play') return;
    const turnsNow = now.turns || [];
    const end = turnsNow[turnsNow.length - 1];
    if (now.turn >= end) {
      set({ replay: { ...now, playing: false } });
      return;
    }
    await showTurn(game, now.turn + 1);
    play._timer = window.setTimeout(tick, 1000 / (state.replay.speed || 1));
  };
  window.clearTimeout(play._timer);
  if (from !== replay.turn) {
    showTurn(game, from).then(() => {
      play._timer = window.setTimeout(tick, 1000 / (state.replay.speed || 1));
    });
  } else {
    play._timer = window.setTimeout(tick, 1000 / (state.replay.speed || 1));
  }
}

export function pause() {
  window.clearTimeout(play._timer);
  set({ replay: { ...state.replay, playing: false } });
}

// --- the board and its controls

function renderReplayBoard(game, record) {
  const card = element('div', { class: 'card' });
  const watching = game.number === 1000 || game.number === 0;
  const units = unitsOf(record);
  const ours = new Set(units.filter((unit) => unit.player === game.number)
    .map((unit) => unit.name));
  const fought = marksFrom(record.events, (name) => ours.has(name));
  const flags = flagsOf(record, units);
  const known = record.known ? knownMap(record) : null;

  card.append(renderBoard(record.board, units, {
    mine: watching ? null : game.number,
    selected: state.selected,
    cursor: state.cursor,
    marks: fought,
    flags,
    watching,
    known,
    hint: true,
    anyUnit: true,
    healthOf: (unit) => ({ now: Number(unit.health),
                           full: Number(unit.type_health) || null }),
    energyOf: (unit) => (Number.isFinite(Number(unit.type_energy))
      && Number(unit.type_energy) > 0
      ? { now: Number(unit.energy), full: Number(unit.type_energy) }
      : null),
    // a click on any unit opens its trace, where this seat is entitled to
    // one, and otherwise says what the unit is
    onUnit: (unit) => {
      const key = `${unit.player}/${unit.name}`;
      set({ selected: state.selected.includes(key) ? [] : [key],
            cursor: { x: unit.x, y: unit.y } });
    },
    onSquare: (x, y) => set({ selected: [], cursor: { x, y } }),
  }));
  card.append(renderControls(game, record));
  return card;
}

/**
 * The scrubber, play, pause, step, speed, and what the board shows.
 *
 * Every control has a key as well as a button - the keyboard help below says
 * which - and the scrubber is a range input, which the keyboard moves on its
 * own. Which turn is shown is said in words beside it, for a reader who
 * cannot see where the thumb is.
 */
function renderControls(game, record) {
  const replay = state.replay;
  const turns = replay.turns || [];
  const first = turns.length ? turns[0] : 0;
  const last = turns.length ? turns[turns.length - 1] : 0;
  const wrap = element('div', { class: 'replay-controls' });

  const scrubber = element('input', {
    type: 'range', min: first, max: last, step: 1, value: replay.turn,
    class: 'scrubber', 'aria-label': 'turn',
    'aria-valuetext': `turn ${replay.turn} of ${last}`,
  });
  scrubber.addEventListener('input', () => {
    pause();
    showTurn(game, Number(scrubber.value));
  });
  wrap.append(element('p', { class: 'scrub-row' },
    element('span', { class: 'turn-label' },
            element('strong', {}, `Turn ${replay.turn}`), ` of ${last}`),
    scrubber));

  const row = element('p', { class: 'replay-buttons' });
  row.append(button('⏮', () => { pause(); showTurn(game, first); },
                    { class: 'control', title: 'first turn (Home)',
                      'aria-label': 'first turn' }));
  row.append(button('◀ step', () => { pause(); stepTurn(game, -1); },
                    { class: 'control', title: 'previous turn (←)',
                      'aria-label': 'previous turn' }));
  row.append(replay.playing
    ? button('❚❚ pause', () => pause(),
             { class: 'control primary', title: 'pause (space)',
               'aria-label': 'pause', 'aria-pressed': 'true' })
    : button('▶ play', () => play(game),
             { class: 'control primary', title: 'play (space)',
               'aria-label': 'play', 'aria-pressed': 'false' }));
  row.append(button('step ▶', () => { pause(); stepTurn(game, 1); },
                    { class: 'control', title: 'next turn (→)',
                      'aria-label': 'next turn' }));
  row.append(button('⏭', () => { pause(); showTurn(game, last); },
                    { class: 'control', title: 'final turn (End)',
                      'aria-label': 'final turn' }));

  const speed = element('select', { class: 'speed', 'aria-label': 'speed',
                                    title: 'speed (+ and -)' });
  for (const option of SPEEDS) {
    speed.append(element('option', { value: option },
                         `${option} turn${option === 1 ? '' : 's'}/s`));
  }
  speed.value = String(replay.speed);
  speed.addEventListener('change', () => {
    set({ replay: { ...state.replay, speed: Number(speed.value) } });
  });
  row.append(element('label', { class: 'inline' }, 'Speed ', speed));
  wrap.append(row);

  // the whole board, or what an army knew of it after this turn. A seat
  // switches its own army's knowledge on and off; the observer and the
  // administrator, who have no army, choose whose
  const watching = game.number === 1000 || game.number === 0;
  const knowRow = element('p', { class: 'known-row' });
  const toggle = element('input', {
    type: 'checkbox', id: 'known-toggle',
  });
  toggle.checked = Boolean(replay.known);
  toggle.addEventListener('change', () => {
    set({ replay: { ...state.replay, known: toggle.checked } });
  });
  knowRow.append(element('label', { for: 'known-toggle', class: 'inline' },
                         toggle,
                         watching ? ' show what an army knew (K)'
                                  : ' show what my army knew (K)'));
  if (watching) {
    const seats = seatsIn(record);
    const whose = element('select', { 'aria-label': 'whose knowledge',
                                      class: 'whose' });
    for (const number of seats) {
      whose.append(element('option', { value: number }, `seat ${number}`));
    }
    whose.value = String(replay.seat || seats[0] || '');
    whose.addEventListener('change', () => {
      set({ replay: { ...state.replay, seat: Number(whose.value) } });
    });
    if (!replay.seat && seats.length) {
      // chosen once, so the toggle has an army to ask about
      state.replay.seat = seats[0];
    }
    knowRow.append(' ', whose);
  }
  wrap.append(knowRow);
  if (record.known) {
    wrap.append(element('p', { class: 'small muted' },
      '? is a square this army has never stood on or fought on; a blank '
      + 'square is one it has walked, E an enemy it remembers where it met '
      + 'it, stamped with the turn.'));
  }
  return wrap;
}

/**
 * The one control that swaps the board for the trays beside it.
 *
 * It says which pane is being shown rather than only what it would do, and
 * says the same thing again when it is pressed, for a reader who is not
 * watching the button change. It is drawn on every screen and hidden by the
 * stylesheet wherever both panes fit, so nothing here has to know the width.
 */
function renderPaneSwitch() {
  const trays = state.pane === 'trays';
  return element('p', { class: 'pane-switch-wrap' },
    button(trays ? 'Traces and forces shown — show the board'
                 : 'Board shown — show traces and forces',
           () => {
             const pane = trays ? 'board' : 'trays';
             set({ pane });
             say(pane === 'trays' ? 'Showing the traces and forces.'
                                  : 'Showing the board.');
           },
           { class: 'pane-switch', 'aria-pressed': trays ? 'true' : 'false' }));
}

// --- reading the record

/** The units of a turn as the board draws them. */
export function unitsOf(record) {
  return (record.units || []).map((unit) => ({
    ...unit,
    // the record's own view carries no design; the type's statistics are
    // read off the types this seat knows, where it knows them
    type_health: unit.type_health,
    type_energy: unit.type_energy,
  }));
}

/** Where every flag stands after a turn: on the unit that carries it. */
export function flagsOf(record, units) {
  const flags = [];
  const seen = new Set();
  for (const unit of units) {
    if (!unit.flag) continue;
    seen.add(unit.player);
    flags.push({ player: unit.player, x: unit.x, y: unit.y, standing: true });
  }
  // a flag the record's legend names on a square no listed unit holds is
  // one the board view drew from the flags file; it is drawn from the rows
  const board = record.board || {};
  (board.legend || []).forEach((entry) => {
    if (entry.type !== 'flag' || seen.has(entry.player)) return;
    (board.rows || []).forEach((row, y) => row.forEach((cell, x) => {
      if (cell === entry.symbol) {
        flags.push({ player: entry.player, x, y, standing: true });
      }
    }));
  });
  return flags;
}

/**
 * The map of the army the known board was drawn for, as the server kept it:
 * the squares the army has stood on with the turn it last did, and the
 * enemies it remembers with the turn they were met and what they were.
 */
function knownMap(record) {
  const map = record.map || {};
  return { visited: map.visited || [], enemies: map.enemies || [] };
}

/** The seats the record holds units for, in order. */
function seatsIn(record) {
  return [...new Set((record.units || []).map((unit) => unit.player))]
    .sort((a, b) => a - b);
}

/** Whether this seat's flag has fallen as the record stands at this turn. */
export function isOutAt(record, number) {
  return (record.eliminated || []).map(Number).includes(Number(number));
}

/**
 * Where the turn was fought, by square.
 *
 * Keyed `x,y`, each holding what to say about that square: how much damage
 * was dealt on it, and which units fell there. A square nobody fought on is
 * not in the map, so the board draws nothing on it.
 */
export function marksFrom(entries, isMine) {
  const mine = isMine || (() => false);
  const marks = new Map();
  for (const entry of entries || []) {
    if (!entry.fighting) continue;
    const { x, y } = entry.detail || {};
    if (x === null || x === undefined || y === null || y === undefined) continue;
    const key = `${x},${y}`;
    const mark = marks.get(key)
      || { x, y, taken: 0, dealt: 0, fallen: [], lost: [] };
    if (entry.kind === 'attacked') {
      const damage = Number(entry.detail.damage) || 0;
      if (mine(entry.detail.target)) mark.taken += damage;
      else mark.dealt += damage;
    }
    if (entry.kind === 'destroyed') {
      mark.fallen.push(entry.detail.unit);
      if (mine(entry.detail.unit)) mark.lost.push(entry.detail.unit);
    }
    marks.set(key, mark);
  }
  return marks;
}

// --- the traces: what each controller did this turn

/**
 * What a controller ordered, in the words a player would use. The engine
 * numbers the headings; a trace carries the number.
 */
export function orderText(order) {
  if (order === null || order === undefined) return 'nothing';
  if (order === 'hold') return 'hold';
  const heading = api.directionByValue(order);
  return heading ? `move ${heading.word}` : String(order);
}

function renderTraces(game, record) {
  const card = element('div', { class: 'card traces' });
  card.append(element('h2', {}, `Controllers on turn ${record.turn}`));
  const traces = record.traces || [];
  const watching = game.number === 1000 || game.number === 0;
  if (!traces.length) {
    card.append(element('p', { class: 'muted small' },
      record.turn === 0
        ? 'Nothing thinks during setup.'
        : (watching ? 'No controller ran this turn.'
                    : 'None of your controllers ran this turn.')));
    return card;
  }
  if (!watching) {
    card.append(element('p', { class: 'small muted' },
      'Your own controllers. Nothing of another seat\'s thinking is shown: '
      + 'contact discloses a type\'s attack, health and energy and nothing '
      + 'of how it thinks.'));
  }
  const chosen = state.selected[0] || null;
  const table = element('table', { class: 'roster' });
  table.append(element('thead', {}, element('tr', {},
    element('th', {}, 'Unit'),
    watching ? element('th', { class: 'number' }, 'Seat') : null,
    element('th', { class: 'number' }, 'Ticks'),
    element('th', { class: 'number' }, 'Energy'),
    element('th', {}, 'Order'),
    element('th', {}, 'Said'),
    element('th', {}, 'Sleep'),
    element('th', {}, 'Halted'))));
  const body = element('tbody', {});
  for (const trace of traces) {
    const key = `${trace.player}/${trace.unit}`;
    const row = element('tr', {
      class: ['trace', key === chosen ? 'chosen' : '',
              trace.halted !== null && trace.halted !== undefined
                ? 'halted' : ''].join(' ').trim(),
      tabindex: '0', role: 'button',
      'aria-pressed': key === chosen ? 'true' : 'false',
      title: `choose ${trace.unit}`,
    });
    const choose = () => {
      const unit = (record.units || []).find(
        (each) => each.player === trace.player && each.name === trace.unit);
      set({ selected: key === chosen ? [] : [key],
            cursor: unit && unit.x !== null ? { x: unit.x, y: unit.y }
                                            : state.cursor });
    };
    row.addEventListener('click', choose);
    row.addEventListener('keydown', (event) => {
      if (event.key === 'Enter' || event.key === ' ') {
        event.preventDefault();
        choose();
      }
    });
    row.append(element('td', {}, trace.unit,
      trace.woken ? element('span', { class: 'tag warn' }, 'woken') : null));
    if (watching) {
      row.append(element('td', { class: 'number' }, String(trace.player)));
    }
    row.append(element('td', { class: 'number' },
                       trace.slept ? '—' : String(trace.ticks)));
    row.append(element('td', { class: 'number' },
                       trace.energy ? `-${trace.energy}` : '0'));
    row.append(element('td', {}, trace.slept ? 'asleep' : orderText(trace.order)));
    row.append(element('td', { class: 'small' }, describeSaid(trace)));
    row.append(element('td', { class: 'small' },
      trace.sleep ? `${trace.sleep} turn${trace.sleep === 1 ? '' : 's'}` : ''));
    row.append(element('td', { class: 'small' },
      trace.halted !== null && trace.halted !== undefined
        ? element('span', { class: 'tag warn' }, `at line ${trace.halted}`)
        : ''));
    body.append(row);
  }
  table.append(body);
  card.append(table);
  if (chosen) {
    const trace = traces.find(
      (each) => `${each.player}/${each.unit}` === chosen);
    if (trace) card.append(renderTraceDetail(trace));
  }
  return card;
}

/** What a controller said, and to whom, in one phrase. */
function describeSaid(trace) {
  const said = trace.said || [];
  const dropped = trace.dropped || [];
  const parts = [];
  if (said.length) {
    parts.push(said.map((words) => `${words[0]}: ${words.slice(1).join(' ')}`)
      .join('; '));
  }
  if (dropped.length) {
    parts.push(`${dropped.length} dropped`);
  }
  return parts.join(' — ');
}

function renderTraceDetail(trace) {
  const box = element('div', { class: 'trace-detail notice' });
  const said = [];
  if (trace.slept) {
    said.push(`${trace.unit} was asleep this turn`
      + (trace.woken ? ', and was woken by a blow' : '') + '.');
  } else {
    said.push(`${trace.unit} thought for ${trace.ticks} ticks`
      + (trace.energy ? `, which charged ${trace.energy} energy` : '')
      + `, and ordered ${orderText(trace.order)}.`);
  }
  if (trace.halted !== null && trace.halted !== undefined) {
    said.push(`Its controller halted at line ${trace.halted}: out of ticks `
      + 'for the turn, or out of energy to think with, so it gave no order '
      + 'and holds.');
  }
  if (trace.sleep) {
    said.push(`It goes to sleep for ${trace.sleep} turn`
      + `${trace.sleep === 1 ? '' : 's'}; a blow wakes it.`);
  }
  for (const words of trace.said || []) {
    said.push(`It said ${words.slice(1).join(', ')} to ${words[0]}.`);
  }
  for (const dropped of trace.dropped || []) {
    said.push(`A message to ${dropped[0]} was dropped: not a friend.`);
  }
  box.append(element('p', { class: 'small' }, said.join(' ')));
  return box;
}

// --- the forces as the record holds them at this turn

function renderForces(game, record) {
  const card = element('div', { class: 'card' });
  card.append(element('h2', {}, 'Forces'));
  const units = record.units || [];
  const players = seatsIn(record);
  for (const player of players) {
    card.append(element('h3', {},
      player === game.number ? 'Yours' : `Player ${player}`));
    card.append(rosterTable(units.filter((unit) => unit.player === player)));
  }
  if (!players.length) {
    card.append(element('p', { class: 'muted small' }, 'Nothing standing.'));
  }
  return card;
}

function rosterTable(units) {
  const table = element('table', { class: 'roster' });
  table.append(element('thead', {}, element('tr', {},
    element('th', {}, 'Unit'),
    element('th', {}, 'Type'),
    element('th', { class: 'number' }, 'Atk'),
    element('th', { class: 'number' }, 'Health'),
    element('th', { class: 'number' }, 'Energy'),
    element('th', {}, 'Where'))));
  const body = element('tbody', {});
  for (const unit of units) {
    body.append(element('tr', {},
      element('td', {}, unit.name,
              unit.flag ? element('span', { class: 'flag-key' }, ' ⚑') : null),
      element('td', {}, unit.type),
      element('td', { class: 'number' }, String(unit.attack)),
      element('td', { class: 'number' }, String(Math.max(0, unit.health))),
      element('td', { class: 'number' }, String(Math.max(0, unit.energy))),
      element('td', { class: 'small' },
        unit.x === null || unit.y === null
          ? element('span', { class: 'muted' }, 'not on the board')
          : `(${unit.x}, ${unit.y})`)));
  }
  table.append(body);
  return table;
}

// --- what the turn did

function renderTurnReport(game, record) {
  const card = element('div', { class: 'card' });
  card.append(element('h2', {}, `What happened on turn ${record.turn}`));

  const refused = record.rejected || [];
  if (refused.length) {
    const list = element('ul', {});
    for (const entry of refused) {
      list.append(element('li', {},
        `${entry.unit} stayed at (${entry.x}, ${entry.y}): ${entry.reason}`));
    }
    card.append(element('div', { class: 'notice' },
      element('strong', {}, 'Orders the turn would not carry out'), list));
  }

  const entries = record.events || [];
  if (!entries.length) {
    card.append(element('p', { class: 'muted' },
      record.turn === 0
        ? 'The setup was committed. Nothing has happened yet.'
        : 'Nothing you could see happened on this turn.'));
    return card;
  }
  const rested = entries.filter((entry) => entry.kind === 'rested');
  const told = entries.filter(
    (entry) => entry.kind !== 'rested' && entry.kind !== 'thought');
  const list = element('ul', { class: 'feed' });
  for (const entry of told) {
    const where = entry.detail || {};
    const line = element('li', {
      class: ['event', entry.kind,
              entry.fighting ? 'fought' : ''].join(' ').trim(),
    });
    line.append(element('span', { class: 'what' }, entry.text));
    if (where.x !== undefined && where.x !== null
        && where.y !== undefined && where.y !== null
        && !/\(\d+, \d+\)/.test(entry.text)) {
      line.append(element('span', { class: 'small muted' },
                          ` at (${where.x}, ${where.y})`));
    }
    list.append(line);
  }
  if (told.length) card.append(list);
  if (rested.length) {
    card.append(element('p', { class: 'small muted' },
      `${rested.length} ${rested.length === 1 ? 'unit' : 'units'} rested and `
      + 'recovered a point of energy.'));
  }
  return card;
}

// --- waiting for the setups, and moving on by itself

/**
 * The board during setup, for a seat that has committed: its own army where
 * it was deployed, faintly, because it is not on the field until the game
 * is resolved.
 */
function renderSetupBoard(game) {
  const card = element('div', { class: 'card' });
  const mine = (game.pending || [])
    .filter((entry) => entry.player === game.number
      && entry.x !== null && entry.y !== null)
    .map((entry) => ({
      player: entry.player, name: entry.unit, type: entry.type,
      symbol: entry.symbol || '?', attack: entry.attack,
      health: entry.health, energy: entry.energy, x: entry.x, y: entry.y,
      pending: true,
    }));
  const units = (game.units || []).concat(mine);
  card.append(renderBoard(game.board, units, {
    mine: game.number,
    flags: game.flags || [],
    watching: game.number === 1000 || game.number === 0,
  }));
  return card;
}

function renderWaiting(game) {
  const card = element('div', { class: 'card' });
  const missing = ((state.waiting && state.waiting.waiting_on)
    || (state.barrier && state.barrier.waiting_on)
    || game.waiting_on || [])
    .filter((number) => number !== game.number);
  const committed = Boolean(game.unprocessed_moves) || game.new_game === false;
  card.append(element('h2', { class: 'waiting' },
    committed ? 'Your setup is committed' : 'The game is being set up'));
  card.append(element('p', {},
    element('strong', {},
            committed ? 'Your army is published. ' : ''),
    missing.length
      ? `Waiting for ${missing.length === 1 ? 'seat' : 'seats'} `
        + `${missing.join(', ')} to commit a setup.`
      : 'Waiting for the game to be resolved.'));
  card.append(element('p', { class: 'small muted' },
    'The game is played to its end the moment the last setup is committed - '
    + 'every turn, by the controllers, with no orders from anybody - and the '
    + 'replay opens here of its own accord. There is nothing to reload.'));
  if (!committed && game.number !== 1000 && game.number !== 0) {
    card.append(element('p', {},
      link('Set up your army',
           `#/setup/${encodeURIComponent(game.gameno)}/${game.number}`,
           { class: 'primary-link' })));
  }
  return card;
}

/**
 * Wait for the resolution, re-issuing the long poll until the game is
 * resolved.
 *
 * The endpoint returns unmet when its budget runs out rather than hanging
 * for ever, so this asks again - which is what keeps a proxy happy and what
 * makes the screen move on without anybody reloading it.
 */
async function watch(game) {
  let missed = 0;
  for (;;) {
    if (state.route.name !== 'play'
        || state.route.gameno !== game.gameno
        || state.route.number !== game.number) return;
    let answer;
    try {
      answer = await api.waitForTurn(game.gameno, game.number, WAIT_BUDGET);
    } catch (error) {
      if (!(await keepTrying(error, ++missed))) return;
      continue;
    }
    if (answer.resolved) {
      // the setup was taken: the game is being, or has been, resolved. Read
      // until the outcome is there - the resolution runs under one hold and
      // may still be running
      for (;;) {
        try {
          await loadSeat(game.gameno, game.number);
        } catch (error) {
          if (!(await keepTrying(error, ++missed))) return;
          continue;
        }
        if (state.game && state.game.outcome) break;
        await new Promise((wake) => window.setTimeout(wake, 1000));
      }
      set({ waiting: null, selected: [], offline: false,
            replay: { ...state.replay, turn: null, record: null } });
      return;
    }
    try {
      const barrier = await api.waitForCommit(game.gameno, game.number,
                                              WAIT_BUDGET);
      missed = 0;
      set({ waiting: barrier, offline: false });
    } catch (error) {
      if (!(await keepTrying(error, ++missed))) return;
    }
  }
}

async function keepTrying(error, missed) {
  if (error && error.notSignedIn) {
    say(error.message);
    return false;
  }
  if (!(error && error.unreachable) && missed > 3) {
    say(error.message);
    return false;
  }
  set({ offline: true });
  const backoff = Math.min(1000 * 2 ** (missed - 1), 15000);
  await new Promise((wake) => window.setTimeout(wake, backoff));
  return true;
}

// --- how the game ended

/**
 * How the game ended, in the words a player would use.
 *
 * `outcome` is `{decided, winner, turn, reason, since}` - a record, not a
 * sentence. An undecided stop says why: the state repeated, or the cap.
 */
export function outcomeText(outcome, seat) {
  if (!outcome) return '';
  if (typeof outcome === 'string') return outcome;
  const turn = outcome.turn ? ` on turn ${outcome.turn}` : '';
  if (outcome.decided === false) {
    const why = outcome.reason === 'repeated'
      ? `its state repeated${outcome.since !== undefined
        && outcome.since !== null
        ? ` (as it stood after turn ${outcome.since})` : ''}`
      : (outcome.reason === 'cap' ? 'the turn cap was reached'
                                  : 'it could not go on');
    return `The game stopped undecided${turn}: ${why}.`;
  }
  if (outcome.winner === null || outcome.winner === undefined) {
    return `Nobody is left standing${turn}. The game is a draw.`;
  }
  if (outcome.winner === seat) {
    return `You won${turn}: yours is the last flag standing.`;
  }
  return `Seat ${outcome.winner} won${turn}.`;
}

function renderOutcome(game, record) {
  const card = element('div', { class: 'card' });
  const final = record === null
    || (state.replay.turns.length
        && record.turn === state.replay.turns[state.replay.turns.length - 1]);
  card.append(element('h2', {}, game.outcome.decided === false
    ? 'The game stopped undecided' : 'The game is decided'));
  card.append(element('p', { class: 'notice' },
                      outcomeText(game.outcome, game.number)));
  card.append(element('p', { class: 'small muted' },
    final
      ? 'This is the final turn. Scrub back, or press play, to watch how it '
        + 'got here.'
      : `Showing turn ${record.turn} of ${game.outcome.turn}.`));
  return card;
}

function renderOut(game) {
  const card = element('div', { class: 'card' });
  card.append(element('h2', {}, 'You are out of the game'));
  card.append(element('p', { class: 'notice' },
    'Your flag has fallen by this turn. A player whose flag carrier is '
    + 'destroyed leaves the game, whatever else they hold.'));
  card.append(element('p', { class: 'small muted' },
    'Your units still hold the squares they stand on, but think nothing and '
    + 'strike nothing. The rest of the record is still yours to watch.'));
  return card;
}

// --- the keyboard
//
// A replay that can only be clicked excludes everybody who does not use a
// mouse, and stepping through turns is faster from the keyboard anyway.

function renderKeys(watching) {
  const card = element('div', { class: 'card keys' });
  card.append(element('p', {},
    element('kbd', {}, '← →'), ' previous and next turn · ',
    element('kbd', {}, 'Space'), ' play and pause · ',
    element('kbd', {}, '+ −'), ' faster and slower · ',
    element('kbd', {}, 'Home End'), ' first and final turn · ',
    element('kbd', {}, 'K'), watching ? ' what an army knew · '
                                      : ' what my army knew · ',
    element('kbd', {}, 'W A S D'), ' move about the board · ',
    element('kbd', {}, 'Enter'), ' read the unit under the cursor · ',
    element('kbd', {}, 'Esc'), ' put it down'));
  card.append(element('p', { class: 'small muted' },
    'Nothing is ordered here: every move in the record was a controller\'s, '
    + 'running its type\'s program. Click a unit, or press Enter over it, to '
    + 'read what its controller did this turn.'));
  return card;
}

export function handleKey(event) {
  const game = state.game;
  if (!game || state.route.name !== 'play' || !game.outcome) return;
  if (event.target && ['INPUT', 'SELECT', 'TEXTAREA']
      .includes(event.target.tagName)) return;
  const replay = state.replay;
  const turns = replay.turns || [];
  if (!turns.length) return;

  if (event.key === 'ArrowLeft') {
    event.preventDefault();
    pause();
    return stepTurn(game, -1);
  }
  if (event.key === 'ArrowRight') {
    event.preventDefault();
    pause();
    return stepTurn(game, 1);
  }
  if (event.key === ' ') {
    event.preventDefault();
    return replay.playing ? pause() : play(game);
  }
  if (event.key === '+' || event.key === '=') {
    event.preventDefault();
    const index = Math.min(SPEEDS.indexOf(replay.speed) + 1, SPEEDS.length - 1);
    return set({ replay: { ...replay, speed: SPEEDS[Math.max(index, 0)] } });
  }
  if (event.key === '-' || event.key === '_') {
    event.preventDefault();
    const index = Math.max(SPEEDS.indexOf(replay.speed) - 1, 0);
    return set({ replay: { ...replay, speed: SPEEDS[index] } });
  }
  if (event.key === 'Home') {
    event.preventDefault();
    pause();
    return showTurn(game, turns[0]);
  }
  if (event.key === 'End') {
    event.preventDefault();
    pause();
    return showTurn(game, turns[turns.length - 1]);
  }
  if (event.key === 'k' || event.key === 'K') {
    event.preventDefault();
    return set({ replay: { ...replay, known: !replay.known } });
  }

  // the cursor moves about the board on WASD, since the arrows move about
  // the record. An arrow key on the board orders nothing: there are no
  // orders
  const step = { w: [0, -1], a: [-1, 0], s: [0, 1], d: [1, 0] }[
    (event.key || '').toLowerCase()];
  if (step && game.board) {
    event.preventDefault();
    const x = Math.min(Math.max(state.cursor.x + step[0], 0),
                       game.board.size_x - 1);
    const y = Math.min(Math.max(state.cursor.y + step[1], 0),
                       game.board.size_y - 1);
    return set({ cursor: { x, y } });
  }

  if (event.key === 'Enter') {
    event.preventDefault();
    const here = ((replay.record && replay.record.units) || []).find(
      (unit) => unit.x === state.cursor.x && unit.y === state.cursor.y);
    return set({ selected: here ? [`${here.player}/${here.name}`] : [] });
  }
  if (event.key === 'Escape') return set({ selected: [] });
  return undefined;
}

window.addEventListener('keydown', handleKey);

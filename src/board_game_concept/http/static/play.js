// The board, the orders tray, the wait, and what the last turn did.
//
// Three rules of the game are shown here rather than left to be discovered,
// because each of them is invisible in the CLI until it has already cost you
// something:
//
//   - what a move costs, before it is committed rather than when the energy
//     has gone;
//   - that a unit given no order recovers a point, so holding is a choice and
//     not an empty row;
//   - that an enemy dropping off the board is contact lost, not a defect.
//
// And three things about the turn that just happened, because a player who
// cannot see them is playing blind:
//
//   - what every unit has left, health as well as energy, on the board and in
//     the tray - a unit one blow from destruction looked exactly like a fresh
//     one;
//   - what the turn did, in the order it did it, from the feed the server
//     wrote for this seat - who struck whom, for how much, and who fell;
//   - where it happened, marked on the squares it happened on, because a list
//     of coordinates is not a picture of a battle.
//
// The last one is the one to be careful with. A player is not entitled to
// remember where an enemy was, so this says contact was lost and draws
// nothing on the square: a remembered position would hand them what the rules
// withhold.

import * as api from './api.js';
import { state, set, say, go, load, loadSeat, element, button,
         link } from './app.js';
import { renderBoard } from './board.js';

const WAIT_BUDGET = 25;

export function renderPlay() {
  const game = state.game;
  if (!game) return element('p', { class: 'waiting' }, 'Loading');

  // this seat has committed and the turn has not resolved, so it is waiting
  // whether or not it was this screen that committed. Arriving from the
  // armoury, or reloading mid-wait, both land here - and a player who had to
  // reload to find out the turn had resolved would rightly call that broken.
  if (game.unprocessed_moves && !state.watching && !game.outcome) {
    state.watching = true;
    watch(game).finally(() => { state.watching = false; });
  }

  const wrap = element('div', {});
  const watching = game.number === 1000;

  wrap.append(element('h1', {},
    `Game ${game.gameno} — `,
    watching ? 'watching' : `seat ${game.number}`,
    game.turn_number ? ` — turn ${game.turn_number}` : ''));
  wrap.append(element('p', {}, link('← lobby', '#/')));

  if (game.outcome) wrap.append(renderOutcome(game));
  else if (isOut(game)) wrap.append(renderOut(game));

  if (!game.board) {
    wrap.append(element('p', { class: 'card muted' }, 'No board yet.'));
    return wrap;
  }

  // the two panes, and the switch between them. On a phone they are one
  // column, so reading the tray meant scrolling the board away and ordering
  // meant scrolling back - to an arrow that had just been drawn off the top
  // of the screen. Which one is shown is this button's; whether it matters
  // is the stylesheet's, and above the width where both fit the button is
  // not there at all and both panes are drawn
  wrap.append(renderPaneSwitch());
  const layout = element('div', { class: `row panes pane-${state.pane}` });
  layout.append(element('div', { class: 'grow board-pane' },
                        renderBoardCard(game)));
  const side = element('div', { class: 'grow tray-pane' });
  if (!watching && !game.outcome && !isOut(game)) {
    side.append(renderOrders(game));
  }
  // the roster is drawn for everybody, watching included: an observer with
  // no orders tray had nowhere at all to read a unit's statistics
  side.append(renderForces(game));
  layout.append(side);
  wrap.append(layout);

  if (game.unprocessed_moves && !game.outcome) {
    wrap.append(renderWaiting(game));
  }
  wrap.append(renderLastTurn(game));
  if (!watching) wrap.append(renderKeys());
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
    button(trays ? 'Orders and forces shown — show the board'
                 : 'Board shown — show orders and forces',
           () => {
             const pane = trays ? 'board' : 'trays';
             set({ pane });
             say(pane === 'trays' ? 'Showing the orders and forces.'
                                  : 'Showing the board.');
           },
           { class: 'pane-switch', 'aria-pressed': trays ? 'true' : 'false' }));
}

/**
 * The army this seat has committed and the turn has not yet placed.
 *
 * Between committing a setup and the first turn resolving, a player's units
 * are published orders and are on no board anywhere: the units view is
 * empty, and this screen drew an empty board and said nothing. They are
 * drawn from the pending orders instead, marked as not yet on the field.
 */
export function committedArmy(game) {
  if (game.turn_number) return [];
  return (game.pending || [])
    .filter((entry) => entry.player === game.number
      && entry.x !== null && entry.y !== null)
    .map((entry) => ({
      player: entry.player,
      name: entry.unit,
      type: entry.type,
      symbol: entry.symbol || '?',
      attack: entry.attack,
      health: entry.health,
      energy: entry.energy,
      x: entry.x,
      y: entry.y,
      state: 'waiting',
      direction: null,
      pending: true,
    }));
}

/**
 * Which way each committed-but-unresolved move points, by unit name.
 *
 * While a player is giving orders the board draws an arrow for each unit
 * under one, read from the `direction` the server replays out of the draft.
 * Committing publishes the draft as orders and clears it, so on the next load
 * the units carry no direction and the arrows vanish - the board snaps back to
 * before anything was ordered, which is exactly what a player who has just
 * committed their plan does not want to see. The orders are not lost: the
 * pending view carries every one, published as the word `move north` and the
 * like, and these read the heading back out so the board can draw the arrow it
 * drew before the commit. Only for a turn past setup - before the first turn a
 * committed army is drawn from pending whole, by `committedArmy`.
 */
export function committedHeadings(game) {
  const headings = {};
  if (!game.unprocessed_moves || !game.turn_number) return headings;
  for (const entry of game.pending || []) {
    if (entry.player !== game.number) continue;
    const match = /^move (north|east|south|west)$/.exec(entry.order || '');
    if (match) headings[entry.unit] = match[1];
  }
  return headings;
}

// --- the forces: what you have, and what you have met
//
// A player deciding whether to attack is comparing two designs, and until
// this card there was nowhere to compare them: your own statistics were in a
// tooltip, and an enemy's vanished from the types list the moment contact was
// lost. What you have met is kept by the server and outlives the contact -
// where an enemy is remains something you are not told.

function renderForces(game) {
  const card = element('div', { class: 'card' });
  card.append(element('h2', {}, 'Forces'));

  const watching = game.number === 1000;
  const units = game.units || [];
  const mine = units.filter((unit) => unit.player === game.number);

  if (watching) {
    const players = [...new Set(units.map((unit) => unit.player))].sort(
      (a, b) => a - b);
    for (const player of players) {
      card.append(element('h3', {}, `Player ${player}`));
      card.append(rosterTable(game, units.filter(
        (unit) => unit.player === player)));
    }
  } else {
    const waiting = committedArmy(game);
    card.append(element('h3', {}, 'Yours'));
    const held = mine.concat(waiting);
    card.append(held.length
      ? rosterTable(game, held)
      : element('p', { class: 'muted small' }, 'Nothing deployed.'));
  }

  const seen = (game.seen || []).filter(
    (type) => watching || type.player !== game.number);
  card.append(element('h3', {}, watching ? 'Every type' : 'Enemy types met'));
  if (!seen.length) {
    card.append(element('p', { class: 'muted small' },
      'None yet. A type is learned by meeting a unit built from it.'));
  } else {
    card.append(typesTable(seen, watching));
  }
  return card;
}

/**
 * Units, with what each has left against what it was built with.
 *
 * Destroyed units are listed and marked rather than dropped: what you have
 * lost is half of what you are assessing.
 */
function rosterTable(game, units) {
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
    const gone = unit.state === 'destroyed';
    body.append(element('tr', { class: gone ? 'gone' : '' },
      element('td', {}, unit.name,
              unit.flag ? element('span', { class: 'flag-key' }, ' ⚑') : null),
      element('td', {}, unit.type),
      element('td', { class: 'number' }, String(unit.attack)),
      element('td', { class: 'number' }, health(game, unit)),
      element('td', { class: 'number' }, String(unit.energy)),
      element('td', { class: 'small' }, gone
        ? element('span', { class: 'tag warn' }, 'destroyed')
        : (unit.pending
          ? element('span', { class: 'tag' }, `committed (${unit.x}, ${unit.y})`)
          : (unit.x === null || unit.y === null
            ? element('span', { class: 'muted' }, 'not deployed')
            : `(${unit.x}, ${unit.y})`)))));
  }
  table.append(body);
  return table;
}

/** Type designs, as they were built rather than as they were met. */
function typesTable(types, watching) {
  const table = element('table', { class: 'roster' });
  table.append(element('thead', {}, element('tr', {},
    element('th', {}, 'Type'),
    element('th', { class: 'number' }, 'Player'),
    element('th', { class: 'number' }, 'Atk'),
    element('th', { class: 'number' }, 'Health'),
    element('th', { class: 'number' }, 'Energy'),
    element('th', { class: 'number' }, 'Cost'),
    element('th', { class: 'small' }, watching ? '' : 'Met'))));
  const body = element('tbody', {});
  for (const type of types) {
    body.append(element('tr', {},
      element('td', {}, `${type.symbol} ${type.name}`),
      element('td', { class: 'number' }, String(type.player)),
      element('td', { class: 'number' }, String(type.attack)),
      element('td', { class: 'number' }, String(type.health)),
      element('td', { class: 'number' }, String(type.energy)),
      element('td', { class: 'number' }, String(type.cost)),
      element('td', { class: 'small muted' },
        type.first_seen === null || type.first_seen === undefined
          ? '' : `turn ${type.first_seen}`)));
  }
  table.append(body);
  return table;
}

// --- what the turns did, as this seat was told it
//
// `state.events` is the feed the server wrote for this seat when each turn
// resolved. Nothing is filtered here: what a seat may be told was decided
// while the turn was being fought, by what it could see at the time.

function turnsInFeed() {
  const turns = new Set();
  for (const entry of state.events || []) turns.add(entry.turn);
  return [...turns].sort((a, b) => a - b);
}

function feedFor(turn) {
  return (state.events || []).filter((entry) => entry.turn === turn);
}

function lastTurnInFeed() {
  const turns = turnsInFeed();
  return turns.length ? turns[turns.length - 1] : null;
}

/**
 * Where the last turn was fought, by square.
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
      // whose blow it was decides which number it belongs to: what a player
      // wants off a board is what it cost *them*, not a total they then have
      // to work out their share of
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

// --- what a move costs, and what a unit has to spend

function typeOf(game, unit) {
  return (game.types || []).find(
    (type) => type.name === unit.type && type.player === unit.player) || null;
}

/**
 * What this unit's type was designed with, from what this seat may know.
 *
 * Its own types are its own; an enemy's is known only where contact has
 * disclosed the design, which is what `seen` holds. A seat that has not met a
 * design is told nothing about it here rather than being handed a maximum it
 * is not entitled to - so a unit whose type is unknown is drawn plainly.
 */
function designOf(game, unit) {
  const own = typeOf(game, unit);
  if (own) return own;
  return (game.seen || []).find(
    (type) => type.name === unit.type && type.player === unit.player) || null;
}

/**
 * What moving costs this unit: a quarter of the health its type was designed
 * with, rounded up.
 *
 * Read off the type rather than restated from the unit's current health,
 * which play wears down - the fare is a property of the design.
 */
export function fareFor(game, unit) {
  const type = typeOf(game, unit);
  if (!type) return null;
  return Math.ceil(Number(type.health) / 4);
}

function myUnits(game) {
  return (game.units || []).filter((unit) => unit.player === game.number);
}

function standing(game) {
  return myUnits(game).filter(
    (unit) => unit.x !== null && unit.y !== null && unit.state !== 'destroyed');
}

// --- the board

function renderBoardCard(game) {
  const card = element('div', { class: 'card' });
  const watching = game.number === 1000;
  const selected = state.selected
    && standing(game).find((unit) => unit.name === state.selected);
  const waiting = committedArmy(game);
  // a committed move leaves its unit standing where it was with its heading
  // cleared, so the arrow is put back from the orders the commit published
  const headings = committedHeadings(game);
  const drawn = (game.units || []).map((unit) => (
    headings[unit.name]
      ? { ...unit, direction: headings[unit.name] }
      : unit)).concat(waiting);

  // who is mine is read off the feed's own names against this seat's units,
  // including units that were destroyed and are no longer on the board
  const ours = new Set(myUnits(game).map((unit) => unit.name));
  const fought = marksFrom(feedFor(lastTurnInFeed()),
                           (name) => ours.has(name));

  card.append(renderBoard(game.board, drawn, {
    mine: game.number,
    selected: state.selected,
    cursor: watching ? null : state.cursor,
    reachable: selected ? reachableFrom(game, selected) : null,
    marks: fought,
    flags: game.flags || [],
    watching,
    // the keyboard hint belongs where a hand already is, which is over the
    // board rather than in a card below it
    hint: !watching && !game.outcome,
    // a unit is drawn with what it has left, which is the whole point of
    // being told the turn wore it down
    healthOf: (unit) => {
      const type = typeOf(game, unit);
      return type ? { now: Number(unit.health), full: Number(type.health) }
                  : { now: Number(unit.health), full: null };
    },
    // and with what it can still pay for, drawn round its ring. An enemy's
    // maximum is only known where contact has disclosed the design
    energyOf: (unit) => {
      const design = designOf(game, unit);
      return design ? { now: Number(unit.energy),
                        full: Number(design.energy) }
                    : null;
    },
    onUnit: watching ? null : (unit) => {
      set({ selected: unit.name, cursor: { x: unit.x, y: unit.y } });
    },
    onSquare: watching ? null : (x, y) => {
      if (!selected) return set({ cursor: { x, y } });
      const direction = api.DIRECTIONS.find(
        (option) => selected.x + option.dx === x && selected.y + option.dy === y);
      if (direction) return order(game, selected, direction);
      return set({ cursor: { x, y } });
    },
    // dragging a unit onto the square next to it is the order it is: a move
    // is one square, so a drop further off is not a longer move, it is a
    // drop that means nothing - and saying so is better than a unit that
    // slides back with no explanation
    onDrop: watching || game.outcome || isOut(game) || game.unprocessed_moves
      ? null
      : (unit, x, y) => {
        const direction = api.DIRECTIONS.find(
          (option) => unit.x + option.dx === x && unit.y + option.dy === y);
        if (!direction) {
          set({ selected: unit.name, cursor: { x: unit.x, y: unit.y } });
          return say(`${unit.name} moves one square at a time — drop it on a `
            + 'square beside the one it stands on.');
        }
        return order(game, unit, direction);
      },
  }));

  // the flag rows of the legend are the grid's way of naming a glyph it drew
  // for a text board; this one draws flags itself and says so below, so
  // repeating them here would name the same thing twice, differently
  const symbols = (game.board.legend || []).filter(
    (entry) => entry.type !== 'flag');
  const legend = element('p', { class: 'small muted' });
  for (const entry of symbols) {
    legend.append(element('span', {},
      `${entry.symbol} = ${entry.type} (player ${entry.player})`), '  ');
  }
  if (symbols.length) card.append(legend);
  if (waiting.length) {
    card.append(element('p', { class: 'small muted' },
      `Your ${waiting.length === 1 ? 'unit is' : 'units are'} drawn where you `
      + 'deployed them and are not on the board yet: a committed setup takes '
      + 'the field when the first turn resolves.'));
  }
  if (Object.keys(headings).length) {
    card.append(element('p', { class: 'small muted' },
      'These are the orders you committed. They cannot be changed, and they '
      + 'resolve when every seat has committed this turn.'));
  }
  const flags = (game.flags || []).filter((flag) => flag.standing);
  if (flags.length) {
    card.append(element('p', { class: 'small muted' },
      element('span', { class: 'flag-key' }, '⚑'),
      ' a flag: '
      + flags.map((flag) => (flag.player === game.number
        ? 'yours'
        : `player ${flag.player}'s`)).join(', ')
      + '. Every flag is shown to everybody; what carries it is not.'));
  }
  if (fought.size) {
    card.append(element('p', { class: 'small muted' },
      element('span', { class: 'clash-key' }, '⚔'),
      ` ${fought.size === 1 ? 'the square' : 'the squares'} last turn was `
      + 'fought on. The number is what it cost you, and ',
      element('span', { class: 'clash-key' }, '☠'),
      ' is where a unit fell.'));
  }

  // the controls that order a unit belong with the board they act on:
  // choosing a unit, ordering it and seeing the arrow drawn are one action,
  // and they used to be a card's width apart
  if (!watching && !game.outcome && !isOut(game)) {
    const chosen = state.selected
      && standing(game).find((unit) => unit.name === state.selected);
    card.append(chosen
      ? renderDirections(game, standing(game))
      : element('p', { class: 'small muted' },
                'Choose one of your units to order it.'));
    // and the commit, beside the controls that gave the orders: the last
    // order and the act that publishes it are one thought, and the button
    // for it was a pane away - past the whole roster on a narrow screen.
    // The same `renderCommit` the tray uses, so the confirmation, the call
    // and what is said afterwards cannot come apart between the two
    card.append(renderCommit(game));
  }
  return card;
}

function reachableFrom(game, unit) {
  return api.DIRECTIONS
    .map((direction) => ({ x: unit.x + direction.dx, y: unit.y + direction.dy }))
    .filter((square) => square.x >= 0 && square.y >= 0
      && square.x < game.board.size_x && square.y < game.board.size_y);
}

async function order(game, unit, direction) {
  try {
    await api.perform(game.gameno, game.number,
                      api.move(unit.name, direction.value));
    await loadSeat(game.gameno, game.number);
    set({ selected: null });
  } catch (error) {
    say(error.message);
  }
}

/**
 * Take back the order a unit was given, while the turn is still being decided.
 *
 * An order was final the moment it was given: a unit ordered north was
 * ordered north, and the only way out was to commit the turn and let it
 * happen. Nothing is final until the turn is committed, so this puts the unit
 * back to having no order at all - which is holding, and rests it.
 */
async function clearOrder(game, unit) {
  try {
    await api.perform(game.gameno, game.number, api.hold(unit.name));
    await loadSeat(game.gameno, game.number);
    say(`${unit.name} holds.`);
  } catch (error) {
    say(error.message);
  }
  set({});
}

// --- the orders tray

function renderOrders(game) {
  const card = element('div', { class: 'card' });
  card.append(element('h2', {}, 'Orders'));

  const units = standing(game);
  if (units.length === 0) {
    const waiting = committedArmy(game);
    card.append(element('p', { class: waiting.length ? 'notice' : 'muted' },
      waiting.length
        ? `Your setup is committed: ${waiting.length} `
          + `${waiting.length === 1 ? 'unit takes' : 'units take'} the field `
          + 'when the first turn resolves. There is nothing to order until '
          + 'then.'
        : 'Nothing of yours is on the board.'));
    return card;
  }

  const table = element('table', { class: 'orders' });
  table.append(element('thead', {}, element('tr', {},
    element('th', {}, 'Unit'),
    element('th', {}, 'Order'),
    element('th', { class: 'number' }, 'Atk'),
    element('th', { class: 'number' }, 'Costs'),
    element('th', { class: 'number' }, 'Health'),
    element('th', { class: 'number' }, 'Energy'),
    element('th', {}, ''))));

  const body = element('tbody', {});
  let spend = 0;
  for (const unit of units) {
    const fare = fareFor(game, unit);
    const ordered = Boolean(unit.direction);
    const affordable = fare === null || unit.energy >= fare;
    if (ordered) spend += fare || 0;

    const row = element('tr', {
      class: [ordered ? '' : 'rest',
              ordered && !affordable ? 'unaffordable' : '',
              unit.name === state.selected ? 'chosen' : ''].join(' ').trim(),
      tabindex: '0',
      role: 'button',
      'aria-pressed': unit.name === state.selected ? 'true' : 'false',
      title: `choose ${unit.name}`,
    });
    // the row selects the unit as well as the board does. On a phone a
    // square is about 32px and a finger is 44, so the tray is the reliable
    // way to choose - and it is where somebody is already reading
    const choose = () => set({
      selected: state.selected === unit.name ? null : unit.name,
      cursor: { x: unit.x, y: unit.y },
    });
    row.addEventListener('click', choose);
    row.addEventListener('keydown', (event) => {
      if (event.key === 'Enter' || event.key === ' ') {
        event.preventDefault();
        choose();
      }
    });
    row.append(element('td', {}, unit.name));
    row.append(element('td', {},
      ordered
        ? element('span', {}, `move ${unit.direction}`)
        : element('span', {}, 'hold')));
    // what a unit hits for, where the decision to send it at an enemy is
    // made. It was in the Forces card, which is a different card and, on a
    // narrow screen, a different screenful
    row.append(element('td', { class: 'number' }, String(unit.attack)));
    row.append(element('td', { class: 'number fare' },
      ordered ? String(fare) : '+1 rest'));
    row.append(element('td', { class: 'number' }, health(game, unit)));
    row.append(element('td', { class: 'number' }, energy(game, unit)));
    row.append(element('td', {}, ordered && !affordable
      ? element('span', { class: 'tag warn' }, 'cannot pay')
      : null));
    body.append(row);
  }
  table.append(body);
  card.append(table);

  card.append(element('p', { class: 'small muted' },
    `${spend} energy will be spent this turn. A unit given no order recovers `
    + 'a point, so holding is a choice.'));

  card.append(renderBarrier(game));
  card.append(renderCommit(game));
  return card;
}

/**
 * Who else has committed, before this seat has.
 *
 * A turn resolves when everybody has committed, and until this said so the
 * only way to find out whether the others were waiting on you was to commit
 * and see.
 */
function renderBarrier(game) {
  const barrier = state.barrier;
  if (!barrier || game.unprocessed_moves) return element('span', {});
  const missing = (barrier.waiting_on || []).filter(
    (number) => number !== game.number);
  if (barrier.met) {
    return element('p', { class: 'small muted' },
      'Every other seat has committed.');
  }
  if (!missing.length) {
    return element('p', { class: 'small muted' },
      'Every other seat has committed. The turn resolves when you do.');
  }
  return element('p', { class: 'small muted' },
    `Still to commit: ${missing.map((number) => `seat ${number}`).join(', ')}.`);
}

/**
 * What a unit has left, against what its type was built with.
 *
 * `8/8` for a unit nobody has touched and `2/10` for one a step from being
 * destroyed - the number that decides whether to fight or fall back, and the
 * one this screen used to keep in a tooltip nobody hovers on a phone.
 */
function health(game, unit) {
  const type = typeOf(game, unit);
  // a destroyed unit is at or below nothing, and "-2 health" is not a thing
  // a person has: it is the overkill of the blow that finished it
  const now = Math.max(0, Number(unit.health));
  if (!type) return element('span', {}, String(now));
  const full = Number(type.health);
  const share = full > 0 ? now / full : 1;
  const cell = element('span', {
    class: ['health', share <= 0.25 ? 'critical' : '',
            share < 1 ? 'hurt' : ''].join(' ').trim(),
    title: share < 1 ? `${full - now} lost of ${full}` : 'unhurt',
  }, `${now}/${full}`);
  return cell;
}

/**
 * What a unit has to spend, against what its type was designed with.
 *
 * `3/5` rather than `3`, the way health is shown beside it: a unit that has
 * been spending and one that has not read alike as a bare number, and the
 * board's ring - which does say - is the thing a player has stopped looking
 * at by the time they are reading this table.
 */
function energy(game, unit) {
  const design = designOf(game, unit);
  const now = Math.max(0, Number(unit.energy));
  if (!design) return element('span', {}, String(now));
  const full = Number(design.energy);
  const share = full > 0 ? now / full : 1;
  return element('span', {
    class: ['power', share <= 0.25 ? 'critical' : '',
            share < 1 ? 'spent' : ''].join(' ').trim(),
    title: share < 1 ? `${full - now} spent of ${full}` : 'unspent',
  }, `${now}/${full}`);
}

/**
 * The five things a unit can be told, laid out as a compass.
 *
 * Four headings around a centre that means "stay where you are". Words in a
 * row had to be read to be used - and read again, because "north" beside
 * "east" is not a direction until you have parsed it. Arrows in the shape of
 * the thing they do are read at a glance, and the centre is where a hand
 * expects "none of these".
 *
 * The centre is always offered, not only for a unit under orders. Holding is
 * a choice a player makes - a unit given no order recovers a point - and it
 * is the same button whether it is choosing to stay or taking back an order
 * given a moment ago.
 */
function renderDirections(game, units) {
  const unit = units.find((each) => each.name === state.selected);
  if (!unit) return element('span', {});
  const wrap = element('div', { class: 'compass-wrap' });
  wrap.append(element('p', { class: 'small' },
    element('strong', {}, unit.name),
    unit.direction ? ` — ordered ${unit.direction}` : ' — holding'));

  const compass = element('div', { class: 'compass' });
  const at = {};
  for (const direction of api.DIRECTIONS) {
    at[direction.word] = button(direction.arrow,
                                () => order(game, unit, direction),
                                { class: 'point',
                                  title: `move ${direction.word}`,
                                  'aria-label': `move ${direction.word}` });
  }
  const hold = button('•', () => clearOrder(game, unit), {
    class: 'point hold' + (unit.direction ? ' undoes' : ''),
    title: unit.direction ? 'take the order back and hold'
                          : 'hold: stay and recover a point',
    'aria-label': unit.direction ? 'take the order back and hold'
                                 : 'hold, staying where it is',
  });
  // laid out as the compass it is: the grid places each one, so the arrows
  // sit where the squares they point at are
  compass.append(element('span', {}), at.north, element('span', {}),
                 at.west, hold, at.east,
                 element('span', {}), at.south, element('span', {}));
  wrap.append(compass);
  return wrap;
}

function renderCommit(game) {
  if (game.unprocessed_moves) {
    return element('p', { class: 'notice small' },
      'Committed. Waiting for the turn to resolve.');
  }
  return element('p', {},
    button('Commit turn', async () => {
      if (!window.confirm(
        'Commit this turn? It cannot be withdrawn or amended.')) return;
      try {
        const answer = await api.commit(game.gameno, game.number);
        // the seat is re-read before anything is drawn. Without it the screen
        // still held the state from before the commit, so it drew the commit
        // button again and said nothing about waiting: the commit had landed
        // and the only way to find that out was to reload the page
        await loadSeat(game.gameno, game.number);
        set({ waiting: answer, selected: null });
        await watch(game);
      } catch (error) {
        say(error.message);
      }
    }, { class: 'primary' }));
}

// --- waiting for the others, and moving on by itself

function renderWaiting(game) {
  const card = element('div', { class: 'card' });
  // whichever of the two knows: the answer to the commit that was just made,
  // or the barrier read when the seat was loaded. Arriving here from the
  // armoury there is no commit answer, and "waiting for the turn to resolve"
  // when it is waiting for a person is the wrong thing to be told
  const missing = ((state.waiting && state.waiting.waiting_on)
    || (state.barrier && state.barrier.waiting_on) || [])
    .filter((number) => number !== game.number);
  const setup = !game.turn_number;
  card.append(element('h2', { class: 'waiting' },
    setup ? 'Your setup is committed'
          : `Turn ${game.turn_number + 1} is committed`));
  card.append(element('p', {},
    element('strong', {},
            setup ? 'Your army is published. ' : 'Your orders are in. '),
    missing.length
      ? `Waiting for ${missing.length === 1 ? 'seat' : 'seats'} ` +
        `${missing.join(', ')} to commit${setup ? ' a setup' : ''}.`
      : 'Waiting for the turn to resolve.'));
  card.append(element('p', { class: 'small muted' },
    'The board moves on by itself when everybody has committed - there is '
    + 'nothing to reload and nothing else to press. An eliminated player is '
    + 'not waited for.'));
  return card;
}

/**
 * Wait for the turn, re-issuing the long poll until it resolves.
 *
 * The endpoint returns unmet when its budget runs out rather than hanging for
 * ever, so this asks again - which is what keeps a proxy happy and what makes
 * the screen move on without anybody reloading it.
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
      const before = state.game;
      await loadSeat(game.gameno, game.number);
      set({ waiting: null, previous: before, selected: null, offline: false });
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

/**
 * What to do about a wait that failed: come back, or stop.
 *
 * A tab used to stop watching for good the first time a poll failed, so a
 * server restarted, a laptop closed, or a poll dropped by something in the
 * middle left a screen that had quietly stopped being a game - and the only
 * way to find out was to reload and see the turn had moved on without you.
 *
 * A refusal is still final: `not signed in` means signing in, not asking
 * again in a moment. Anything that is nobody answering is worth asking again,
 * backing off so a server that is down is not hammered while it comes back.
 */
async function keepTrying(error, missed) {
  if (error && error.notSignedIn) {
    say(error.message);
    return false;
  }
  if (!(error && error.unreachable) && missed > 3) {
    // a refusal that keeps coming back is not a connection problem
    say(error.message);
    return false;
  }
  set({ offline: true });
  const backoff = Math.min(1000 * 2 ** (missed - 1), 15000);
  await new Promise((wake) => window.setTimeout(wake, backoff));
  return true;
}

// --- what the turns did

function renderLastTurn(game) {
  const card = element('div', { class: 'card' });
  const turns = turnsInFeed();
  const latest = lastTurnInFeed();

  card.append(element('h2', {}, latest === null
    ? 'What happened'
    : `What happened on turn ${latest}`));

  const refused = game.rejected || [];
  const dropped = game.dropped || [];
  const lost = lostContact(game);

  if (refused.length) {
    const list = element('ul', {});
    for (const entry of refused) {
      list.append(element('li', {},
        `${entry.unit} stayed at (${entry.x}, ${entry.y}): ${entry.reason}`));
    }
    card.append(element('div', { class: 'notice' },
      element('strong', {}, 'Orders the turn would not carry out'), list));
  }

  if (dropped.length) {
    const list = element('ul', {});
    for (const entry of dropped) list.append(element('li', {}, entry.message));
    card.append(element('div', { class: 'notice' },
      element('strong', {}, 'Work that could not be replayed'), list));
  }

  if (latest === null) {
    card.append(element('p', { class: 'muted' },
      game.turn_number
        ? 'Nothing was reported for the last turn.'
        : 'The game has not started yet.'));
  } else {
    card.append(renderTurn(game, latest));
  }

  if (lost.length) {
    card.append(element('div', { class: 'lost' },
      element('strong', {}, 'Contact lost'),
      element('p', { class: 'small' },
        `You no longer see ${lost.join(', ')}. Visibility is wiped at the ` +
        'start of every turn, so an enemy you did not touch this turn drops ' +
        'off your board. You are not told where they went.')));
  }

  // the turns before the last one. Folded away rather than dropped: what a
  // player wants nine times in ten is the turn that just happened, and the
  // tenth time is the one where they are trying to work out how they got
  // here - and that is exactly when a history that was never kept hurts
  const earlier = turns.slice(0, -1).reverse();
  if (earlier.length) {
    card.append(element('p', {},
      button(state.showHistory
        ? 'hide earlier turns'
        : `earlier turns (${earlier.length})`,
        () => set({ showHistory: !state.showHistory }),
        { class: 'link' })));
    if (state.showHistory) {
      for (const turn of earlier) {
        const past = element('div', { class: 'past-turn' });
        past.append(element('h3', {}, `Turn ${turn}`));
        past.append(renderTurn(game, turn));
        card.append(past);
      }
    }
  }
  return card;
}

/**
 * One turn of the feed, in the order it happened.
 *
 * A blow is drawn as a blow and a move as a move, because a player scanning
 * this wants the fighting first and the manoeuvring as context. Resting is
 * counted rather than listed: ten units recovering a point each is ten lines
 * saying nothing, and the one line saying it is the one worth reading.
 */
function renderTurn(game, turn) {
  const entries = feedFor(turn);
  const wrap = element('div', {});
  if (entries.length === 0) {
    wrap.append(element('p', { class: 'muted' },
      'Nothing you could see happened on this turn.'));
    return wrap;
  }

  const rested = entries.filter((entry) => entry.kind === 'rested');
  const told = entries.filter((entry) => entry.kind !== 'rested');

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
  if (told.length) wrap.append(list);

  if (rested.length) {
    wrap.append(element('p', { class: 'small muted' },
      `${rested.length} ${rested.length === 1 ? 'unit' : 'units'} rested and `
      + 'recovered a point of energy.'));
  }
  return wrap;
}

/**
 * Enemy units that were in this seat's view last turn and are not now.
 *
 * Named rather than drawn: `visibility` wipes every sighting at the start of
 * each resolution, so a unit that is gone is gone, and putting a ghost where
 * it stood would be a memory the rules do not grant.
 */
function lostContact(game) {
  if (!state.previous || !state.previous.units) return [];
  const now = new Set((game.units || [])
    .filter((unit) => unit.player !== game.number)
    .map((unit) => `${unit.player}/${unit.name}`));
  return state.previous.units
    .filter((unit) => unit.player !== game.number)
    .filter((unit) => !now.has(`${unit.player}/${unit.name}`))
    .map((unit) => unit.name);
}

/**
 * How the game ended, in the words a player would use.
 *
 * `outcome` is `{decided, winner, turn}` - a record, not a sentence. Putting
 * it on the page as it stood printed `[object Object]`, which is the one
 * thing a player who has just won or lost should not be told.
 */
export function outcomeText(outcome, seat) {
  if (!outcome) return '';
  if (typeof outcome === 'string') return outcome;
  const turn = outcome.turn ? ` on turn ${outcome.turn}` : '';
  if (outcome.winner === null || outcome.winner === undefined) {
    return `Nobody is left standing${turn}. The game is a draw.`;
  }
  if (outcome.winner === seat) {
    return `You won${turn}: yours are the last units standing.`;
  }
  return `Seat ${outcome.winner} won${turn}. Nothing of yours is left `
    + 'standing.';
}

/**
 * Whether this seat is out of the game.
 *
 * Its flag has fallen: the published flags say so, and they say so to
 * everybody. Nothing else is needed - a player whose flag is down is out
 * whatever else they still hold.
 */
export function isOut(game) {
  const mine = (game.flags || []).find(
    (flag) => flag.player === game.number);
  return Boolean(mine) && mine.standing === false;
}

function renderOut(game) {
  const card = element('div', { class: 'card' });
  card.append(element('h2', {}, 'You are out of the game'));
  card.append(element('p', { class: 'notice' },
    'Your flag has fallen. A player whose flag carrier is destroyed leaves '
    + 'the game, whatever else they hold.'));
  card.append(element('p', { class: 'small muted' },
    'Your units are still on the board and hold the squares they stand on, '
    + 'but they take no orders and strike nothing. The board and what each '
    + 'turn does keep arriving here for as long as you want to watch.'));
  return card;
}

function renderOutcome(game) {
  const card = element('div', { class: 'card' });
  card.append(element('h2', {}, 'The game is decided'));
  card.append(element('p', { class: 'notice' },
                      outcomeText(game.outcome, game.number)));
  card.append(element('p', { class: 'small muted' },
    'No further order or commit is accepted. The final board is below.'));
  return card;
}

// --- the keyboard
//
// A grid that can only be clicked excludes everybody who does not use a
// mouse, and for a game this close to chess it is simply faster.

function renderKeys() {
  const card = element('div', { class: 'card keys' });
  card.append(element('p', {},
    element('kbd', {}, '← ↑ → ↓'), ' move about the board · ',
    element('kbd', {}, 'Enter'), ' select the unit under the cursor · ',
    element('kbd', {}, 'Esc'), ' clear the selection · ',
    element('kbd', {}, 'Del'), ' take back its order · ',
    element('kbd', {}, 'C'), ' commit'));
  card.append(element('p', { class: 'small muted' },
    'With a unit selected, an arrow key orders it that way, and '
    + 'Delete takes the order back until the turn is committed.'));
  return card;
}

export function handleKey(event) {
  const game = state.game;
  if (!game || state.route.name !== 'play' || game.number === 1000) return;
  if (game.outcome || isOut(game)) return;
  if (event.target && ['INPUT', 'SELECT', 'TEXTAREA']
      .includes(event.target.tagName)) return;

  const arrow = {
    ArrowUp: 'north', ArrowRight: 'east',
    ArrowDown: 'south', ArrowLeft: 'west',
  }[event.key];

  if (arrow) {
    event.preventDefault();
    const direction = api.directionByWord(arrow);
    const selected = standing(game).find(
      (unit) => unit.name === state.selected);
    if (selected) return order(game, selected, direction);
    const x = Math.min(Math.max(state.cursor.x + direction.dx, 0),
                       game.board.size_x - 1);
    const y = Math.min(Math.max(state.cursor.y + direction.dy, 0),
                       game.board.size_y - 1);
    return set({ cursor: { x, y } });
  }

  if (event.key === 'Enter') {
    event.preventDefault();
    const here = standing(game).find(
      (unit) => unit.x === state.cursor.x && unit.y === state.cursor.y);
    return set({ selected: here ? here.name : null });
  }

  // Backspace and Delete take back the order the selected unit was given,
  // which is where a hand already is after the arrow keys that gave it
  if (event.key === 'Backspace' || event.key === 'Delete') {
    event.preventDefault();
    const chosen = standing(game).find(
      (unit) => unit.name === state.selected);
    if (chosen && chosen.direction) return clearOrder(game, chosen);
    return undefined;
  }

  if (event.key === 'Escape') return set({ selected: null });

  // the commit is offered twice now - under the compass and under the
  // orders tray - and both are the same `renderCommit`, so pressing the
  // first is pressing either. The board's pane is drawn first, which is
  // where a hand on `c` is already looking. A third primary button on this
  // screen would make this the wrong one, so it would need a selector of
  // its own rather than the first of whatever is there
  if (event.key === 'c' || event.key === 'C') {
    event.preventDefault();
    const commit = document.querySelector('button.primary');
    if (commit) commit.click();
  }
  return undefined;
}

window.addEventListener('keydown', handleKey);

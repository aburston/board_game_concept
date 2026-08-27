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

  if (!game.board) {
    wrap.append(element('p', { class: 'card muted' }, 'No board yet.'));
    return wrap;
  }

  const layout = element('div', { class: 'row' });
  layout.append(element('div', { class: 'grow' }, renderBoardCard(game)));
  if (!watching && !game.outcome) {
    layout.append(element('div', { class: 'grow' }, renderOrders(game)));
  }
  wrap.append(layout);

  if (game.unprocessed_moves && !game.outcome) {
    wrap.append(renderWaiting(game));
  }
  wrap.append(renderLastTurn(game));
  if (!watching) wrap.append(renderKeys());
  return wrap;
}

// --- what a move costs, and what a unit has to spend

function typeOf(game, unit) {
  return (game.types || []).find(
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

  card.append(renderBoard(game.board, game.units, {
    mine: game.number,
    selected: state.selected,
    cursor: watching ? null : state.cursor,
    reachable: selected ? reachableFrom(game, selected) : null,
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
  }));

  const legend = element('p', { class: 'small muted' });
  for (const entry of (game.board.legend || [])) {
    legend.append(element('span', {},
      `${entry.symbol} = ${entry.type} (player ${entry.player})`), '  ');
  }
  if ((game.board.legend || []).length) card.append(legend);
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

// --- the orders tray

function renderOrders(game) {
  const card = element('div', { class: 'card' });
  card.append(element('h2', {}, 'Orders'));

  const units = standing(game);
  if (units.length === 0) {
    card.append(element('p', { class: 'muted' },
      'Nothing of yours is on the board.'));
    return card;
  }

  const table = element('table', { class: 'orders' });
  table.append(element('thead', {}, element('tr', {},
    element('th', {}, 'Unit'),
    element('th', {}, 'Order'),
    element('th', { class: 'number' }, 'Costs'),
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
    row.append(element('td', { class: 'number fare' },
      ordered ? String(fare) : '+1 rest'));
    row.append(element('td', { class: 'number' }, String(unit.energy)));
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

  if (state.selected) {
    card.append(renderDirections(game, units));
  } else {
    card.append(element('p', { class: 'small muted' },
      'Choose one of your units to order it.'));
  }

  card.append(renderCommit(game));
  return card;
}

function renderDirections(game, units) {
  const unit = units.find((each) => each.name === state.selected);
  if (!unit) return element('span', {});
  const row = element('p', {});
  row.append(element('strong', {}, unit.name), ' ');
  for (const direction of api.DIRECTIONS) {
    row.append(button(`${direction.arrow} ${direction.word}`,
                      () => order(game, unit, direction)), ' ');
  }
  return row;
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
  const missing = (state.waiting && state.waiting.waiting_on) || [];
  card.append(element('h2', { class: 'waiting' }, 'Waiting'));
  card.append(element('p', {}, missing.length
    ? `Waiting for ${missing.length === 1 ? 'seat' : 'seats'} ` +
      `${missing.join(', ')} to commit.`
    : 'Waiting for the turn to resolve.'));
  card.append(element('p', { class: 'small muted' },
    'An eliminated player is not waited for.'));
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
  for (;;) {
    if (state.route.name !== 'play'
        || state.route.gameno !== game.gameno
        || state.route.number !== game.number) return;
    let answer;
    try {
      answer = await api.waitForTurn(game.gameno, game.number, WAIT_BUDGET);
    } catch (error) {
      say(error.message);
      return;
    }
    if (answer.resolved) {
      const before = state.game;
      await loadSeat(game.gameno, game.number);
      set({ waiting: null, previous: before, selected: null });
      return;
    }
    try {
      const barrier = await api.waitForCommit(game.gameno, game.number,
                                              WAIT_BUDGET);
      set({ waiting: barrier });
    } catch (error) {
      say(error.message);
      return;
    }
  }
}

// --- what the last turn did

function renderLastTurn(game) {
  const card = element('div', { class: 'card' });
  card.append(element('h2', {}, 'Last turn'));

  const refused = game.rejected || [];
  const dropped = game.dropped || [];
  const lost = lostContact(game);
  let said = false;

  if (refused.length) {
    said = true;
    const list = element('ul', {});
    for (const entry of refused) {
      list.append(element('li', {},
        `${entry.unit} stayed at (${entry.x}, ${entry.y}): ${entry.reason}`));
    }
    card.append(element('div', { class: 'notice' },
      element('strong', {}, 'Orders the turn would not carry out'), list));
  }

  if (dropped.length) {
    said = true;
    const list = element('ul', {});
    for (const entry of dropped) list.append(element('li', {}, entry.message));
    card.append(element('div', { class: 'notice' },
      element('strong', {}, 'Work that could not be replayed'), list));
  }

  if (lost.length) {
    said = true;
    card.append(element('div', { class: 'lost' },
      element('strong', {}, 'Contact lost'),
      element('p', { class: 'small' },
        `You no longer see ${lost.join(', ')}. Visibility is wiped at the ` +
        'start of every turn, so an enemy you did not touch this turn drops ' +
        'off your board. You are not told where they went.')));
  }

  if (!said) {
    card.append(element('p', { class: 'muted' },
      game.turn_number
        ? 'Nothing of yours was refused, and nothing dropped out of view.'
        : 'The game has not started yet.'));
  }
  return card;
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

function renderOutcome(game) {
  const card = element('div', { class: 'card' });
  card.append(element('h2', {}, 'The game is decided'));
  card.append(element('p', { class: 'notice' }, game.outcome));
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
    element('kbd', {}, 'C'), ' commit'));
  card.append(element('p', { class: 'small muted' },
    'With a unit selected, an arrow key orders it that way.'));
  return card;
}

export function handleKey(event) {
  const game = state.game;
  if (!game || state.route.name !== 'play' || game.number === 1000) return;
  if (game.outcome) return;
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

  if (event.key === 'Escape') return set({ selected: null });

  if (event.key === 'c' || event.key === 'C') {
    event.preventDefault();
    const commit = document.querySelector('button.primary');
    if (commit) commit.click();
  }
  return undefined;
}

window.addEventListener('keydown', handleKey);

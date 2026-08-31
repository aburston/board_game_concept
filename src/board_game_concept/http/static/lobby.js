// The lobby: which games exist, which seats are open, and taking one.
//
// A game is listed whether or not you hold a seat in it, because a seat
// cannot be found before it is held.

import * as api from './api.js';
import { state, set, say, go, load, element, button, link } from './app.js';

export function renderLobby() {
  const wrap = element('div', {});
  wrap.append(element('h1', {}, 'Games'));

  if (state.account.kind === 'admin') wrap.append(renderCreate());

  if (state.games.length === 0) {
    wrap.append(element('p', { class: 'card muted' },
      state.account.kind === 'admin'
        ? 'No games yet. Make one above.'
        : 'No games yet. The administrator makes them.'));
    return wrap;
  }

  for (const game of state.games) wrap.append(renderGame(game));
  return wrap;
}

/**
 * The lowest game number that is free, from 1 up.
 *
 * The same offer the setup screen makes for a seat, for the same reason: the
 * number of the next game is one the lobby already knows, and typing it was a
 * chance to collide with a game that exists - which the server refuses, after
 * the form has been sent.
 *
 * The lowest free rather than one past the highest, so a number that has been
 * given up is used again rather than left as a gap for ever. A game may be
 * called anything the server accepts; this only decides what is offered, and
 * a number typed over it is what gets created.
 */
function nextGameno(games) {
  const taken = new Set((games || []).map((game) => String(game.gameno)));
  let number = 1;
  while (taken.has(String(number))) number += 1;
  return number;
}

function renderCreate() {
  const card = element('div', { class: 'card' });
  const input = element('input', { type: 'text', placeholder: 'game number' });
  // held in `state` like every other half-made choice: the lobby is redrawn
  // whenever a game is listed again, and a number half-typed was lost to it
  input.value = state.newGameno || String(nextGameno(state.games));
  input.addEventListener('input', () => {
    state.newGameno = input.value;
  });
  const form = element('form', { class: 'row' });
  form.append(element('label', { class: 'grow' }, 'New game', input),
              element('p', {},
                      element('button', { class: 'primary', type: 'submit' },
                              'Create')));
  form.addEventListener('submit', async (event) => {
    event.preventDefault();
    try {
      await api.createGame(input.value.trim());
      // made, so the field goes back to offering the next free number
      // rather than the one that has just been used
      state.newGameno = '';
      await load();
    } catch (error) {
      say(error.message);
    }
  });
  card.append(form);
  return card;
}

function mySeats(game) {
  const held = (state.account.seats || [])
    .filter((seat) => String(seat.gameno) === String(game.gameno));
  return held.map((seat) => seat.number);
}

function renderGame(game) {
  const card = element('div', { class: 'card' });
  const mine = mySeats(game);

  const heading = element('h2', {}, `Game ${game.gameno}`);
  heading.append(' ', element('span', { class: 'tag' }, game.state));
  if (game.size_x) {
    heading.append(' ', element('span', { class: 'small muted' },
                                `${game.size_x}×${game.size_y}`));
  }
  if (game.turn_number) {
    heading.append(' ', element('span', { class: 'small muted' },
                                `turn ${game.turn_number}`));
  }
  if (mine.length) heading.append(' ', element('span', { class: 'tag mine' },
                                               'yours'));
  const waited = game.seats.filter((seat) => seat.held_by && !seat.committed);
  if (game.state === 'setting up' && mine.length
      && game.seats.some((seat) => mine.includes(seat.number)
                                   && seat.committed)) {
    heading.append(' ', element('span', { class: 'tag' }, 'committed'));
  }
  if (state.account.kind === 'admin' && game.state === 'setting up') {
    heading.append(' ', element('span', { class: 'tag' },
                                game.setup_committed ? 'setup committed'
                                                     : 'not set up yet'));
  }
  card.append(heading);

  if (game.state === 'unreadable') {
    card.append(element('p', { class: 'lost' },
      `This game cannot be read: ${game.error || 'unknown reason'}`));
    return card;
  }

  if (game.outcome) {
    card.append(element('p', { class: 'notice' }, game.outcome));
  }

  if (game.seats.length === 0) {
    card.append(element('p', { class: 'muted small' },
      'No seats yet — the administrator has not registered any players.'));
  } else {
    card.append(renderSeats(game, mine));
  }

  if (game.state === 'setting up' && game.open_seats > 0) {
    card.append(element('p', { class: 'small muted' },
      `${game.open_seats} of ${game.seats.length} seats still open.`));
  }
  if (state.account.kind === 'admin' && game.state === 'setting up'
      && game.setup_committed) {
    card.append(element('p', { class: 'small muted' },
      'This game is set up: the board is published and the seats are fixed. '
      + 'It starts when every seat is held and every player has committed.'));
  }
  if (game.state === 'setting up' && game.open_seats === 0 && waited.length) {
    card.append(element('p', { class: 'small muted' },
      `Waiting for ${waited.length === 1 ? 'seat' : 'seats'} `
      + `${waited.map((seat) => seat.number).join(', ')} to commit a setup. `
      + 'The first turn resolves when they have.'));
  }

  // until the administrator's commit ends it there is a setup to do; after
  // it, every command that screen could send would be refused, and offering
  // it was offering a dead end.
  //
  // This used to ask whether the game had a board, because a board was stored
  // by that commit and by nothing else. A created game is given one now, so
  // that question answered "committed" for every new game and the setup
  // screen could not be reached at all
  if (state.account.kind === 'admin' && !game.setup_committed) {
    card.append(element('p', {},
      link('Set this game up', `#/setup/${encodeURIComponent(game.gameno)}/0`,
           { class: 'small' })));
  }
  if (state.account.kind === 'observer' || state.account.kind === 'admin') {
    card.append(element('p', {},
      link('Watch', `#/play/${encodeURIComponent(game.gameno)}/1000`,
           { class: 'small' })));
  }
  return card;
}

function renderSeats(game, mine) {
  const table = element('table', {});
  table.append(element('thead', {}, element('tr', {},
    element('th', { class: 'number' }, 'Seat'),
    element('th', {}, 'Held by'),
    element('th', {}, ''))));

  const body = element('tbody', {});
  for (const seat of game.seats) {
    const isMine = mine.includes(seat.number);
    const row = element('tr', {});
    row.append(element('td', { class: 'number' }, String(seat.number)));
    row.append(element('td', {},
      seat.held_by
        ? element('span', {}, seat.held_by,
                  isMine ? element('span', { class: 'tag mine' }, ' you') : null)
        : element('span', { class: 'tag open' }, 'open')));
    row.append(element('td', {}, seatAction(game, seat, isMine)));
    body.append(row);
  }
  table.append(body);
  return table;
}

// Whether this account may hold a seat at all, which is what decides whether
// a seat is offered to be taken. Asked as one question rather than as a list
// of kinds, because the server answers it as one: a seat is a membership row
// and the row does not record what kind of account holds it, so the only
// account that may not hold one is the observer - which is 1000 of every game
// and holds no seat in any. Enumerating the kinds that may instead meant the
// button was drawn from a list that could fall out of step with the refusal.
function mayHoldASeat(account) {
  return account.kind !== 'observer';
}

function seatAction(game, seat, isMine) {
  if (isMine) {
    // a seat that has committed goes to the board, whatever the game is
    // doing. Sending it back to the armoury - because the game is still
    // "setting up" until somebody else commits - landed a player on a
    // screen where every command they could give would be refused
    const where = game.state === 'setting up' && !seat.committed
      ? 'setup' : 'play';
    const actions = element('span', {},
      link('Play', `#/${where}/${encodeURIComponent(game.gameno)}/${seat.number}`));
    if (game.state === 'setting up' && !seat.committed) {
      actions.append(' ', button('give up', async () => {
        try {
          await api.releaseSeat(game.gameno, seat.number);
          await load();
        } catch (error) {
          say(error.message);
        }
      }, { class: 'danger small' }));
    }
    return actions;
  }
  if (seat.held_by) return element('span', { class: 'muted small' }, '—');
  if (!mayHoldASeat(state.account)) {
    return element('span', { class: 'muted small' }, '—');
  }
  if (game.state !== 'setting up') {
    return element('span', { class: 'muted small' }, 'game has started');
  }
  return button('take seat', async () => {
    try {
      await api.claimSeat(game.gameno, seat.number);
      await load();
      go(`#/setup/${encodeURIComponent(game.gameno)}/${seat.number}`);
    } catch (error) {
      say(error.message);
      await load();
    }
  }, { class: 'primary' });
}

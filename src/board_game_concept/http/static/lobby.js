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

function renderCreate() {
  const card = element('div', { class: 'card' });
  const input = element('input', { type: 'text', placeholder: 'game number' });
  const form = element('form', { class: 'row' });
  form.append(element('label', { class: 'grow' }, 'New game', input),
              element('p', {},
                      element('button', { class: 'primary', type: 'submit' },
                              'Create')));
  form.addEventListener('submit', async (event) => {
    event.preventDefault();
    try {
      await api.createGame(input.value.trim());
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
  if (game.state === 'setting up' && game.open_seats === 0 && waited.length) {
    card.append(element('p', { class: 'small muted' },
      `Waiting for ${waited.length === 1 ? 'seat' : 'seats'} `
      + `${waited.map((seat) => seat.number).join(', ')} to commit a setup. `
      + 'The first turn resolves when they have.'));
  }

  if (state.account.kind === 'admin') {
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
  if (state.account.kind !== 'player' && state.account.kind !== 'admin') {
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

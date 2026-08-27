// Setup: designing unit types, and deploying units within a budget.
//
// The cost of a type is the sum of its three statistics, and it is shown as
// they are chosen rather than when the type is defined - the trade the budget
// exists to make is only a trade if you can see it while you are making it.
//
// The administrator's setup - sizing the board and registering players - is
// the same screen, because it is the same phase and the same commands.

import * as api from './api.js';
import { state, set, say, go, load, loadSeat, element, button, field,
         link } from './app.js';
import { renderBoard } from './board.js';

export function renderArmoury() {
  const game = state.game;
  const wrap = element('div', {});
  if (!game) return element('p', { class: 'waiting' }, 'Loading');

  wrap.append(element('h1', {},
    `Game ${game.gameno} — `,
    game.number === 0 ? 'setting up' : `seat ${game.number}`));
  wrap.append(element('p', {}, link('← lobby', '#/')));

  if (game.number === 0) {
    wrap.append(renderAdminSetup(game));
    return wrap;
  }

  if (!game.board) {
    wrap.append(element('p', { class: 'card notice' },
      'The administrator has not sized the board yet. ' +
      'You can design types now and deploy once there is a board.'));
  }

  wrap.append(renderBudget(game));
  wrap.append(renderDesigner(game));
  wrap.append(renderTypes(game));
  if (game.board) wrap.append(renderDeploy(game));
  wrap.append(renderCommit(game));
  return wrap;
}

// --- the administrator's half

function renderAdminSetup(game) {
  const card = element('div', { class: 'card' });
  card.append(element('h2', {}, 'The board'));
  if (game.board) {
    card.append(element('p', { class: 'muted' },
      `Sized ${game.board.size_x}×${game.board.size_y}. ` +
      'A board that exists cannot be resized.'));
  } else {
    const x = field('Width (2–10)', 'number');
    const y = field('Height (2–10)', 'number');
    const form = element('form', { class: 'row' });
    form.append(element('div', { class: 'grow' }, x.label),
                element('div', { class: 'grow' }, y.label),
                element('p', {}, element('button',
                  { class: 'primary', type: 'submit' }, 'Set board')));
    form.addEventListener('submit', send(game,
      () => api.setBoard(Number(x.input.value), Number(y.input.value))));
    card.append(form);
  }

  card.append(element('h2', {}, 'Seats'));
  card.append(element('p', { class: 'small muted' },
    'A seat is a player number. Register them here; people take them from ' +
    'the lobby. No player can be added once the game has started.'));

  const registered = game.players || [];
  if (registered.length) {
    const table = element('table', {});
    table.append(element('thead', {}, element('tr', {},
      element('th', { class: 'number' }, 'Seat'),
      element('th', { class: 'number' }, 'Budget'))));
    const body = element('tbody', {});
    for (const player of registered) {
      body.append(element('tr', {},
        element('td', { class: 'number' }, String(player.player)),
        element('td', { class: 'number' },
                player.budget === null ? '—' : String(player.budget))));
    }
    table.append(body);
    card.append(table);
  }

  const number = field('Seat number (1–999)', 'number');
  const budget = field('Budget (default 100)', 'number');
  const form = element('form', { class: 'row' });
  form.append(element('div', { class: 'grow' }, number.label),
              element('div', { class: 'grow' }, budget.label),
              element('p', {}, element('button', { type: 'submit' },
                                       'Add seat')));
  form.addEventListener('submit', send(game, () => api.addPlayer(
    Number(number.input.value),
    budget.input.value === '' ? 100 : Number(budget.input.value))));
  card.append(form);

  card.append(element('h2', {}, 'Finish setup'));
  card.append(element('p', { class: 'small muted' },
    'Committing ends setup and publishes the board. Seats can still be ' +
    'taken until the first turn resolves.'));
  card.append(button('Commit setup', async () => {
    try {
      await api.commit(game.gameno, 0);
      await load();
      say('Setup committed.');
    } catch (error) {
      say(error.message);
    }
  }, { class: 'primary' }));
  return card;
}

// --- the player's half

function costOf(type) {
  return Number(type.attack) + Number(type.health) + Number(type.energy);
}

function me(game) {
  return (game.players || []).find(
    (player) => player.player === game.number) || {};
}

function renderBudget(game) {
  const mine = me(game);
  const card = element('div', { class: 'card' });
  card.append(element('h2', {}, 'Budget'));
  if (mine.budget === null || mine.budget === undefined) {
    card.append(element('p', { class: 'muted' }, 'No budget to show.'));
    return card;
  }
  const spent = Number(mine.spent || 0);
  const left = Number(mine.left);
  const bar = element('div', { class: 'meter' },
    element('span', { style: `width: ${Math.min(100, 100 * spent / mine.budget)}%` }));
  card.append(bar);
  card.append(element('p', { class: 'small' },
    `${spent} spent of ${mine.budget} — `,
    element('strong', {}, `${left} left`)));
  return card;
}

function renderDesigner(game) {
  const card = element('div', { class: 'card' });
  card.append(element('h2', {}, 'Design a type'));

  // every input reads its value from `state.design` and writes back on the
  // way through, so a redraw - a refusal, a reload of the views - finds the
  // design where it left it
  const bind = (label, type, key) => {
    const made = field(label, type);
    made.input.value = state.design[key];
    made.input.addEventListener('input', () => {
      state.design[key] = made.input.value;
    });
    return made;
  };
  const name = bind('Name', 'text', 'name');
  const symbol = bind('Symbol (one character)', 'text', 'symbol');
  const attack = bind('Attack', 'number', 'attack');
  const health = bind('Health', 'number', 'health');
  const energy = bind('Energy', 'number', 'energy');

  const cost = element('strong', {}, '3');
  const price = element('p', { class: 'small' }, 'Costs ', cost, ' points — ',
    element('span', { class: 'muted' }, 'attack + health + energy'));

  // the cost moves as the design is chosen: this is what makes the trade
  // visible while it is being made rather than after it is refused
  const recost = () => {
    const total = Number(attack.input.value || 0)
      + Number(health.input.value || 0) + Number(energy.input.value || 0);
    cost.textContent = String(total);
    const left = Number(me(game).left);
    price.classList.toggle('unaffordable',
                           Number.isFinite(left) && total > left);
  };
  for (const stat of [attack, health, energy]) {
    stat.input.addEventListener('input', recost);
  }

  const form = element('form', {});
  form.append(element('div', { class: 'row' },
    element('div', { class: 'grow' }, name.label),
    element('div', { class: 'grow' }, symbol.label)));
  form.append(element('div', { class: 'row' },
    element('div', { class: 'grow' }, attack.label),
    element('div', { class: 'grow' }, health.label),
    element('div', { class: 'grow' }, energy.label)));
  form.append(price);
  form.append(element('p', { class: 'small muted' },
    'A type with less energy than health can never move and never strike — ' +
    'it holds a square and nothing else.'));
  form.append(element('p', {},
    element('button', { class: 'primary', type: 'submit' }, 'Define type')));
  form.addEventListener('submit', send(game, () => api.addType(
    name.input.value.trim(), symbol.input.value.trim(),
    Number(attack.input.value), Number(health.input.value),
    Number(energy.input.value)), () => {
      // only once it was accepted: a refusal leaves the design to be fixed
      state.design = { name: '', symbol: '', attack: '1', health: '1',
                       energy: '1' };
    }));
  card.append(form);
  recost();
  return card;
}

function renderTypes(game) {
  const card = element('div', { class: 'card' });
  card.append(element('h2', {}, 'Your types'));
  const mine = (game.types || []).filter(
    (type) => type.player === game.number);
  if (mine.length === 0) {
    card.append(element('p', { class: 'muted' },
      'None yet. Defining a type is free; deploying is what spends.'));
    return card;
  }
  const left = Number(me(game).left);
  const table = element('table', {});
  table.append(element('thead', {}, element('tr', {},
    element('th', {}, 'Name'), element('th', {}, 'Symbol'),
    element('th', { class: 'number' }, 'Atk'),
    element('th', { class: 'number' }, 'HP'),
    element('th', { class: 'number' }, 'Energy'),
    element('th', { class: 'number' }, 'Cost'),
    element('th', {}, ''))));
  const body = element('tbody', {});
  for (const type of mine) {
    const cost = costOf(type);
    const affordable = !Number.isFinite(left) || cost <= left;
    body.append(element('tr', {},
      element('td', {}, type.name),
      element('td', {}, type.symbol),
      element('td', { class: 'number' }, String(type.attack)),
      element('td', { class: 'number' }, String(type.health)),
      element('td', { class: 'number' }, String(type.energy)),
      element('td', { class: 'number' }, String(cost)),
      element('td', {}, affordable
        ? element('span', { class: 'tag mine' }, 'affordable')
        : element('span', { class: 'tag warn' }, 'too dear'))));
  }
  table.append(body);
  card.append(table);
  return card;
}

function renderDeploy(game) {
  const card = element('div', { class: 'card' });
  card.append(element('h2', {}, 'Deploy'));
  const mine = (game.types || []).filter(
    (type) => type.player === game.number);
  if (mine.length === 0) {
    card.append(element('p', { class: 'muted' },
      'Design a type first.'));
    return card;
  }

  const chooser = element('select', {});
  for (const type of mine) {
    chooser.append(element('option', { value: type.name },
                           `${type.name} — ${costOf(type)} points`));
  }
  const unitName = field('Unit name', 'text');
  unitName.input.value = state.unitName;
  unitName.input.addEventListener('input', () => {
    state.unitName = unitName.input.value;
  });
  card.append(element('div', { class: 'row' },
    element('div', { class: 'grow' }, element('label', {}, 'Type', chooser)),
    element('div', { class: 'grow' }, unitName.label)));
  card.append(element('p', { class: 'small muted' },
    'Then choose a square on the board.'));

  card.append(renderBoard(game.board, game.units, {
    mine: game.number,
    onSquare: async (x, y) => {
      const name = unitName.input.value.trim()
        || `${chooser.value}-${(game.units || []).length + 1}`;
      try {
        await api.perform(game.gameno, game.number,
                          api.addUnit(chooser.value, name, x, y));
        state.unitName = '';
        await loadSeat(game.gameno, game.number);
        say(`${name} deployed at (${x}, ${y}).`);
      } catch (error) {
        say(error.message);
      }
    },
  }));
  return card;
}

function renderCommit(game) {
  const card = element('div', { class: 'card' });
  card.append(element('h2', {}, 'Commit'));
  card.append(element('p', { class: 'small muted' },
    'Committing publishes your army for the first turn. It cannot be ' +
    'withdrawn or amended.'));
  card.append(button('Commit setup', async () => {
    if (!window.confirm(
      'Commit? This cannot be withdrawn or amended.')) return;
    try {
      await api.commit(game.gameno, game.number);
      go(`#/play/${encodeURIComponent(game.gameno)}/${game.number}`);
      await load();
    } catch (error) {
      say(error.message);
    }
  }, { class: 'primary' }));
  return card;
}

// --- one shape for every form that sends a command

function send(game, build, accepted) {
  return async (event) => {
    event.preventDefault();
    try {
      await api.perform(game.gameno, game.number, build());
      if (accepted) accepted();
      await loadSeat(game.gameno, game.number);
      say(null);
    } catch (error) {
      say(error.message);
    }
    // the whole screen is redrawn from state, never patched in place
    set({});
  };
}

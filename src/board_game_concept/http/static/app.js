// One state object, one render, and no code outside `render` touching the DOM.
//
// That rule is the whole of the discipline here, and nothing enforces it, so
// it is written down: a framework's job is to make partial updates safe, and
// without one the cheapest way to stay correct is not to do partial updates
// at all. The board is at most 10x10, so redrawing everything on every change
// costs nothing a person can perceive.
//
// The seat is read from the address every time and never held in `state` as a
// "current seat": one account may hold several seats of one game, so two tabs
// are two seats, and a shared current-seat would make them fight.

import * as api from './api.js';
import { renderLobby } from './lobby.js';
import { renderArmoury } from './armoury.js';
import { renderPlay } from './play.js';

// --- the state
//
// Everything the page draws is in here. Nothing is read back out of the DOM.

export const state = {
  route: { name: 'loading' },
  account: null,
  games: [],
  game: null,          // the seat's own view: board, units, types, state
  previous: null,      // the board as it was last turn, for what changed
  selected: null,      // the name of the unit being ordered
  // what is half-typed in the armoury. In `state` rather than in the DOM
  // because `render` replaces the whole screen: a refusal redraws, and a
  // form rebuilt from nothing would throw away the design somebody was in
  // the middle of - which is the moment they are most likely to give up
  design: { name: '', symbol: '', attack: '1', health: '1', energy: '1' },
  unitName: '',
  deployType: '',      // the type being deployed, kept across placements
  boardSize: { x: '', y: '' },   // a size typed and not yet sent
  cursor: { x: 0, y: 0 },
  waiting: null,       // {met, waiting_on} while a commit is outstanding
  watching: false,     // whether a wait loop is already running
  events: [],          // what the turns did, as this seat was told it
  flagChoice: '',      // the unit being designated in the armoury
  showHistory: false,  // whether the feed is showing turns before the last
  barrier: null,       // {met, waiting_on}: who this turn is still waiting on
  offline: false,      // whether the server has stopped answering
  message: null,
  busy: false,
};

export function set(changes) {
  Object.assign(state, changes);
  render();
}

export function say(message) {
  state.message = message;
  render();
  if (message) {
    window.clearTimeout(say._timer);
    say._timer = window.setTimeout(() => set({ message: null }), 6000);
  }
}

// --- the address is the route
//
// `#/` the lobby, `#/setup/<gameno>/<number>` the armoury, and
// `#/play/<gameno>/<number>` a seat at the board.

export function parseRoute(hash) {
  const parts = (hash || '').replace(/^#\/?/, '').split('/').filter(Boolean);
  if (parts.length === 0) return { name: 'lobby' };
  if (parts[0] === 'setup' && parts.length === 3) {
    return { name: 'setup', gameno: decodeURIComponent(parts[1]),
             number: Number(parts[2]) };
  }
  if (parts[0] === 'play' && parts.length === 3) {
    return { name: 'play', gameno: decodeURIComponent(parts[1]),
             number: Number(parts[2]) };
  }
  if (parts[0] === 'password') return { name: 'password' };
  return { name: 'lobby' };
}

export function go(hash) {
  if (window.location.hash === hash) {
    load();
  } else {
    window.location.hash = hash;
  }
}

// --- loading what the route needs

export async function load() {
  const route = parseRoute(window.location.hash);
  state.route = route;
  state.busy = true;
  render();          // draws `loading` until `whoami` says who is asking

  try {
    state.account = await api.whoami();
    state.offline = false;
  } catch (error) {
    if (error.notSignedIn) {
      state.account = null;
      state.route = { name: 'signIn' };
      state.busy = false;
      return render();
    }
    if (error.unreachable) {
      // the page used to throw here and stay on `Loading` for ever, which is
      // what a server restarted under an open tab looked like
      state.offline = true;
      state.busy = false;
      retryLoad();
      return render();
    }
    throw error;
  }

  // an account that must change its password may do nothing else, so there is
  // nowhere else for it to be
  if (state.account.must_change_password && route.name !== 'password') {
    state.route = { name: 'password' };
    state.busy = false;
    return render();
  }

  try {
    if (route.name === 'lobby') {
      state.games = (await api.listGames()).games;
      state.game = null;
      state.previous = null;
    } else if (route.name === 'setup' || route.name === 'play') {
      await loadSeat(route.gameno, route.number);
    }
  } catch (error) {
    if (error.notSignedIn) {
      state.account = null;
      state.route = { name: 'signIn' };
    } else if (error.unreachable) {
      state.offline = true;
      retryLoad();
    } else {
      state.message = error.message;
    }
  }
  state.busy = false;
  return render();
}

// how long to leave it before asking again, doubling to a cap. A page nobody
// is watching should not sit hammering a server that is down
let waited = 0;

function retryLoad() {
  waited = Math.min(waited ? waited * 2 : 1000, 15000);
  window.clearTimeout(retryLoad._timer);
  retryLoad._timer = window.setTimeout(() => {
    if (!state.offline) return;
    load();
  }, waited);
}

export async function loadSeat(gameno, number) {
  // `board`, `units` and `pending` all need a board, and a game being set up
  // does not have one yet - the server says 404 and means "not yet" rather
  // than "no such thing". `types` and `players` answer either way, which is
  // what the armoury needs before a board exists.
  const absent = (error) => (error.status === 404 ? null : Promise.reject(error));
  const [seatState, board, units, types, players, pending, seen, flags,
         events, barrier] = await Promise.all([
    api.readState(gameno, number),
    api.readView(gameno, number, 'board').catch(absent),
    api.readView(gameno, number, 'units').catch(absent),
    api.readView(gameno, number, 'types'),
    api.readView(gameno, number, 'players'),
    // the orders that have been published and not yet resolved. Between
    // committing a setup and the first turn an army is on no board at all,
    // and this is the only place it can be read from
    api.readView(gameno, number, 'pending').catch(absent),
    // what this seat has met, which outlives contact with it. The types
    // view is what is in contact now; this is what is known
    api.readView(gameno, number, 'designs').catch(absent),
    // every flag in the game, whoever it belongs to: the one thing shown
    // without contact, so it does not travel inside this seat's own view
    api.readView(gameno, number, 'flags').catch(absent),
    // the feed is a history rather than a snapshot, so it is fetched with
    // everything else: a screen that has to ask for it separately is a
    // screen that draws a board and then changes its mind about it
    api.readView(gameno, number, 'events').catch(absent),
    // who has committed, asked with no budget so it answers at once. A
    // player deciding whether to think for another minute wants to know
    // whether everyone else is already waiting on them
    api.waitForCommit(gameno, number, 0).catch(() => null),
  ]);
  const previous = state.game && state.game.gameno === gameno
    && state.game.number === number ? state.game : null;
  state.previous = previous;
  state.events = (events && events.events) || [];
  state.barrier = barrier || null;
  state.game = {
    gameno,
    number,
    ...seatState,
    board: board ? board.board : null,
    units: units ? units.units : [],
    types: types.types,
    players: players.players,
    pending: (pending && pending.pending) || [],
    seen: (seen && seen.designs) || [],
    flags: (flags && flags.flags) || [],
  };
}

// --- rendering
//
// One function. Every screen returns a node, and the whole main element is
// replaced by it.

const screens = {
  loading: () => element('p', { class: 'waiting' }, 'Loading'),
  signIn: renderSignIn,
  password: renderPassword,
  lobby: renderLobby,
  setup: renderArmoury,
  play: renderPlay,
};

export function render() {
  const main = document.getElementById('screen');
  const chrome = document.getElementById('chrome');
  const whoami = document.getElementById('whoami');
  const say_ = document.getElementById('say');

  chrome.hidden = !state.account;
  whoami.replaceChildren();
  if (state.account) {
    whoami.append(
      element('span', {}, `${state.account.username} (${state.account.kind})`),
      ' · ',
      button('sign out', async () => {
        await api.signOut();
        set({ account: null, route: { name: 'signIn' } });
      }, { class: 'link' }));
  }

  say_.hidden = !state.message;
  say_.textContent = state.message || '';

  // no screen is drawn without an account. Every screen but these two reads
  // `state.account`, and `load()` renders once before it knows who is asking
  // - so the guard belongs here rather than at the top of each screen, where
  // the one that forgot it would be the one that broke the page.
  let name = state.route.name;
  if (!state.account && name !== 'signIn' && name !== 'loading') {
    name = state.busy ? 'loading' : 'signIn';
  }
  const screen = screens[name] || renderLobby;
  main.replaceChildren(screen());
  // drawn here rather than by a screen, because losing the server is not
  // something one screen has and the others do not
  if (state.offline) main.prepend(renderOffline());
}

/**
 * Said while the server is not answering.
 *
 * A page that has lost the server looks exactly like a page where nothing is
 * happening, so it has to say so - and say that it is still trying, because
 * it is, and that nothing committed is lost, because nothing is.
 */
function renderOffline() {
  return element('div', { class: 'card notice offline' },
    element('strong', {}, 'Not reaching the server. '),
    'Still trying — this picks up where it left off when the server answers '
    + 'again. Nothing you have committed is lost.');
}

// --- the two screens that belong to nobody else

function renderSignIn() {
  const wrap = element('div', { class: 'card' });
  wrap.append(element('h1', {}, 'Sign in'));

  const username = field('Username', 'text', 'username');
  const password = field('Password', 'password', 'current-password');
  const form = element('form', {});
  form.append(username.label, password.label,
              element('p', {},
                      element('button', { class: 'primary', type: 'submit' },
                              'Sign in'),
                      ' ',
                      button('Register instead', () =>
                        set({ route: { name: 'signIn', registering: true } }))));
  form.addEventListener('submit', async (event) => {
    event.preventDefault();
    try {
      await api.signIn(username.input.value, password.input.value);
      go('#/');
      await load();
    } catch (error) {
      say(error.message);
    }
  });
  wrap.append(form);

  if (state.route.registering) {
    const rName = field('New username', 'text', 'username');
    const rPass = field('New password (8 or more)', 'password',
                        'new-password');
    const rForm = element('form', {});
    rForm.append(element('h2', {}, 'Register'), rName.label, rPass.label,
                 element('p', {},
                         element('button', { type: 'submit' }, 'Register')));
    rForm.addEventListener('submit', async (event) => {
      event.preventDefault();
      try {
        await api.register(rName.input.value, rPass.input.value);
        await api.signIn(rName.input.value, rPass.input.value);
        go('#/');
        await load();
      } catch (error) {
        say(error.message);
      }
    });
    wrap.append(rForm);
  }

  wrap.append(element('p', { class: 'small muted' },
    'The observer account sees every unit of every player, on every game. ' +
    'Nothing stops somebody who holds a seat from using it, so it is left ' +
    'to the honesty of the people playing.'));
  return wrap;
}

function renderPassword() {
  const wrap = element('div', { class: 'card' });
  wrap.append(element('h1', {}, 'Change your password'));
  wrap.append(element('p', { class: 'notice' },
    `${state.account.username} was created with a password everybody knows. ` +
    'It must be changed before this account can do anything else.'));

  const current = field('Current password', 'password', 'current-password');
  const next = field('New password (8 or more)', 'password', 'new-password');
  const form = element('form', {});
  form.append(current.label, next.label,
              element('p', {},
                      element('button', { class: 'primary', type: 'submit' },
                              'Change it')));
  form.addEventListener('submit', async (event) => {
    event.preventDefault();
    try {
      await api.changePassword(current.input.value, next.input.value);
      go('#/');
      await load();
    } catch (error) {
      say(error.message);
    }
  });
  wrap.append(form);
  return wrap;
}

// --- small builders, so the screens read as what they draw

export function element(tag, attributes, ...children) {
  const node = document.createElement(tag);
  for (const [name, value] of Object.entries(attributes || {})) {
    if (value === null || value === undefined || value === false) continue;
    if (name === 'hidden' || name === 'disabled') node[name] = Boolean(value);
    else node.setAttribute(name, value);
  }
  for (const child of children.flat()) {
    if (child === null || child === undefined || child === false) continue;
    node.append(child);
  }
  return node;
}

export function button(text, onClick, attributes) {
  const node = element('button', { type: 'button', ...(attributes || {}) },
                       text);
  node.addEventListener('click', onClick);
  return node;
}

export function field(labelText, type, autocomplete) {
  const input = element('input', { type, autocomplete: autocomplete || 'off' });
  const label = element('label', {}, labelText, input);
  return { label, input };
}

export function link(text, hash, attributes) {
  return element('a', { href: hash, ...(attributes || {}) }, text);
}

// --- start

window.addEventListener('hashchange', () => { load(); });
window.addEventListener('DOMContentLoaded', () => { load(); });
if (document.readyState !== 'loading') load();

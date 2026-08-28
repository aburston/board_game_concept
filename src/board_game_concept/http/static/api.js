// Every call this page makes, in one file, each named for the contract
// endpoint it calls. Nothing else in the page speaks to the server, so what
// the interface depends on can be read here in one sitting - and anything it
// cannot do is a gap in the contract rather than a reason for a private route.
//
// The credential is the session cookie the server set when we signed in. It is
// HttpOnly, so this file never sees a token and never has anywhere to leak one
// from; a command-line role sends the same token as a bearer header instead.

export class ApiError extends Error {
  constructor(status, body) {
    super((body && body.error) || `request failed (${status})`);
    this.status = status;
    this.body = body || {};
  }

  get mustChangePassword() {
    return this.status === 403 && this.body.must_change_password === true;
  }

  get notSignedIn() {
    return this.status === 401;
  }
}

/**
 * A request the server never answered: it was restarted, the network went, or
 * the browser gave up on it.
 *
 * Told apart from a refusal on purpose. A refusal is the server saying no and
 * is the caller's to deal with; this is nobody saying anything, and the only
 * sensible answer to it is to ask again in a moment.
 */
export class Unreachable extends Error {
  constructor(cause) {
    super('the server did not answer');
    this.cause = cause;
    this.unreachable = true;
  }
}

// how long to wait for an answer before deciding there is not going to be
// one. The long polls are deliberately longer than this and say so
const PATIENCE = 15000;

async function call(method, path, body, patience) {
  const options = { method, headers: {}, credentials: 'same-origin' };
  if (body !== undefined) {
    options.headers['Content-Type'] = 'application/json';
    options.body = JSON.stringify(body);
  }
  // a request with nothing behind it hangs until the browser decides, which
  // on a dropped connection is minutes. The screen is left saying nothing at
  // all in the meantime, which is what "it lost the server" looks like
  const limit = patience === undefined ? PATIENCE : patience;
  const giveUp = new AbortController();
  const timer = window.setTimeout(() => giveUp.abort(), limit);
  options.signal = giveUp.signal;

  let response;
  try {
    response = await fetch(path, options);
  } catch (error) {
    throw new Unreachable(error);
  } finally {
    window.clearTimeout(timer);
  }

  const text = await response.text();
  let parsed = null;
  if (text) {
    try { parsed = JSON.parse(text); } catch { parsed = null; }
  }
  if (!response.ok) throw new ApiError(response.status, parsed);
  return parsed;
}

const get = (path) => call('GET', path);
const post = (path, body) => call('POST', path, body);
const remove = (path) => call('DELETE', path);

// --- accounts

export const register = (username, password) =>
  post('/accounts', { username, password });

export const signIn = (username, password) =>
  post('/sessions', { username, password });

export const signOut = () => remove('/sessions/current');

export const whoami = () => get('/accounts/current');

export const changePassword = (current, next) =>
  post('/accounts/current/password', { current, new: next });

// --- the lobby

export const listGames = () => get('/games');

export const createGame = (gameno) => post('/games', { gameno });

export const claimSeat = (gameno, number) =>
  post(`/games/${encodeURIComponent(gameno)}/seats/${number}`);

export const releaseSeat = (gameno, number) =>
  remove(`/games/${encodeURIComponent(gameno)}/seats/${number}`);

// --- one seat of one game
//
// The number is in the path because one account may hold several seats of one
// game, so the account does not say which seat it is acting as.

const seatPath = (gameno, number) =>
  `/games/${encodeURIComponent(gameno)}/players/${number}`;

export const readState = (gameno, number) =>
  get(`${seatPath(gameno, number)}/state`);

export const readView = (gameno, number, subject) =>
  get(`${seatPath(gameno, number)}/views/${subject}`);

export const perform = (gameno, number, command) =>
  post(`${seatPath(gameno, number)}/commands`, command);

export const commit = (gameno, number) =>
  post(`${seatPath(gameno, number)}/commit`);

// the long polls, which are meant to take as long as their budget. They are
// given that budget plus a margin to answer in, rather than the patience an
// ordinary request gets, which they would exceed by design
const waitPatience = (budget) => (Number(budget) + 10) * 1000;

export const waitForTurn = (gameno, number, budget) =>
  call('GET', `${seatPath(gameno, number)}/wait/turn?budget=${budget}`,
       undefined, waitPatience(budget));

export const waitForCommit = (gameno, number, budget) =>
  call('GET', `${seatPath(gameno, number)}/wait/commit?budget=${budget}`,
       undefined, waitPatience(budget));

// --- the commands, as the records `service/commands.py` reads back
//
// Built here rather than at each call site, so the wire shape of a command is
// stated once and matches `as_record` exactly.

export const setBoard = (sizeX, sizeY) =>
  ({ kind: 'set_board', size_x: sizeX, size_y: sizeY });

export const addPlayer = (number, budget) =>
  ({ kind: 'add_player', number, budget });

export const removePlayer = (number) =>
  ({ kind: 'remove_player', number });

export const addType = (name, symbol, attack, health, energy) =>
  ({ kind: 'add_type', name, symbol, attack, health, energy });

export const addUnit = (typeName, name, x, y) =>
  ({ kind: 'add_unit', type_name: typeName, name, x, y });

export const move = (unit, direction) => ({ kind: 'move', unit, direction });

export const setFlag = (unit) => ({ kind: 'set_flag', unit });

// what the engine calls each direction, and what a person calls it
export const DIRECTIONS = [
  { key: 'north', word: 'north', value: 1, dx: 0, dy: -1, arrow: '↑' },
  { key: 'east', word: 'east', value: 2, dx: 1, dy: 0, arrow: '→' },
  { key: 'south', word: 'south', value: 3, dx: 0, dy: 1, arrow: '↓' },
  { key: 'west', word: 'west', value: 4, dx: -1, dy: 0, arrow: '←' },
];

export const directionByWord = (word) =>
  DIRECTIONS.find((direction) => direction.word === word) || null;

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

async function call(method, path, body) {
  const options = { method, headers: {}, credentials: 'same-origin' };
  if (body !== undefined) {
    options.headers['Content-Type'] = 'application/json';
    options.body = JSON.stringify(body);
  }
  const response = await fetch(path, options);
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

export const waitForTurn = (gameno, number, budget) =>
  get(`${seatPath(gameno, number)}/wait/turn?budget=${budget}`);

export const waitForCommit = (gameno, number, budget) =>
  get(`${seatPath(gameno, number)}/wait/commit?budget=${budget}`);

// --- the commands, as the records `service/commands.py` reads back
//
// Built here rather than at each call site, so the wire shape of a command is
// stated once and matches `as_record` exactly.

export const setBoard = (sizeX, sizeY) =>
  ({ kind: 'set_board', size_x: sizeX, size_y: sizeY });

export const addPlayer = (number, budget) =>
  ({ kind: 'add_player', number, budget });

export const addType = (name, symbol, attack, health, energy) =>
  ({ kind: 'add_type', name, symbol, attack, health, energy });

export const addUnit = (typeName, name, x, y) =>
  ({ kind: 'add_unit', type_name: typeName, name, x, y });

export const move = (unit, direction) => ({ kind: 'move', unit, direction });

// what the engine calls each direction, and what a person calls it
export const DIRECTIONS = [
  { key: 'north', word: 'north', value: 1, dx: 0, dy: -1, arrow: '↑' },
  { key: 'east', word: 'east', value: 2, dx: 1, dy: 0, arrow: '→' },
  { key: 'south', word: 'south', value: 3, dx: 0, dy: 1, arrow: '↓' },
  { key: 'west', word: 'west', value: 4, dx: -1, dy: 0, arrow: '←' },
];

export const directionByWord = (word) =>
  DIRECTIONS.find((direction) => direction.word === word) || null;

// The board: one <svg>, squares drawn once, a <g> per unit positioned by
// transform.
//
// Moving a unit between turns is a change of that transform, and the CSS
// transition on it is the whole animation - no timeline, no frame loop, no
// library. `prefers-reduced-motion` turns it off. The replay leans on this:
// drawing the next turn's record moves every unit from its old square to its
// new one, which is what makes a turn visible rather than only its result.
//
// This file draws what the view gives it and never decides what to conceal.
// A seat's published view already holds only what that seat may see, and a
// turn of the record is drawn whole for everybody because `visibility` grants
// the whole board once a game is finished - so everything here has already
// been filtered where it is decided, and a board that tried to be clever
// about hiding would be a second opinion on a question that already has an
// answer.
//
// Nothing here orders anything. A player gives no orders - every move is a
// controller's, running its type's program - so a click on a unit chooses it
// and nothing more, and the box, the double-click and the arrow that an order
// used to be drawn with are gone with the orders.

const NS = 'http://www.w3.org/2000/svg';

const SQUARE = 44;
const PAD = 6;

// the ring is smaller than the square it stands in, so that what is drawn
// round it - the energy arc, the health bar - has somewhere to be drawn
const RING = SQUARE / 2 - 11;

// where the energy arc runs, outside the ring and touching nothing. Stroked
// at 3, so it occupies 12.5 to 15.5 from the centre of a square: clear of the
// ring's outer edge at 12, and clear of the health bar, whose lower edge is
// 16 from the centre. Half a square is 22, so it is well inside its own
const ARC = RING + 3;

// how far the pointer travels before a click becomes a drag. Without it every
// tap on a unit is a one-pixel drag, and choosing a unit - the thing done
// most often - stops working
const DRAG_THRESHOLD = 4;

// what a square of an army's map is drawn with when the map is all the army
// knows of it, as `service/replay.py` writes them
const UNKNOWN_SYMBOL = '?';
const ENEMY_SYMBOL = 'E';

/**
 * Which band a share of something falls in: green, amber or red.
 *
 * One function for both of the things drawn round a unit, so energy and
 * health are read on one scale rather than two.
 *
 * A boundary belongs to the worse band - a unit at exactly a third is red,
 * and at exactly two thirds amber - because a player reading a unit should
 * not be told it is fine when it is on the line.
 */
function band(share) {
  if (share > 2 / 3) return 'full';
  if (share > 1 / 3) return 'low';
  return 'spent';
}

function svg(tag, attributes) {
  const node = document.createElementNS(NS, tag);
  for (const [name, value] of Object.entries(attributes || {})) {
    if (value === null || value === undefined) continue;
    node.setAttribute(name, String(value));
  }
  return node;
}

export function emptySymbol(board) {
  // the glyph an empty square is drawn with is the domain's to choose, so it
  // is asked for rather than assumed here. The scan is the fallback for a
  // view drawn before the field existed - and it is only a fallback because
  // it guesses a flag's glyph on a board whose first square holds one
  if (board.empty) return board.empty;
  for (const row of board.rows) {
    for (const cell of row) if (cell) return cell;
  }
  return ' ';
}

/**
 * Draw a board.
 *
 * `options` carries what the screen knows and the board does not: whose seat
 * this is, which unit is chosen, where the keyboard cursor is, and what to do
 * when a square or a unit is chosen. `known` is the board as an army knew it,
 * drawn over the squares: unknown squares and remembered enemies, from the
 * record's map.
 */
export function renderBoard(board, units, options) {
  const settings = options || {};
  const mine = settings.mine;
  const selected = new Set(settings.selected || []);
  const width = board.size_x * SQUARE + PAD * 2;
  const height = board.size_y * SQUARE + PAD * 2;

  const root = svg('svg', {
    // a watching session owns none of the units, so "yours and theirs" says
    // nothing to it and every unit was drawn as an enemy. It is told to
    // colour by player instead
    class: 'board' + (settings.watching ? ' watching' : '')
      + (settings.known ? ' known' : ''),
    viewBox: `0 0 ${width} ${height}`,
    width,
    height,
    role: 'grid',
    'aria-label': `board, ${board.size_x} by ${board.size_y}`,
  });

  const empty = emptySymbol(board);
  const marks = settings.marks || new Map();
  const flags = (settings.flags || []).filter(
    (flag) => flag.standing && flag.x !== null && flag.y !== null);
  const known = settings.known || null;
  const squares = svg('g', { class: 'squares' });
  for (let y = 0; y < board.size_y; y += 1) {
    for (let x = 0; x < board.size_x; x += 1) {
      const knowledge = known ? knownAt(known, x, y) : null;
      const rect = svg('rect', {
        class: 'square'
          + (isOutOfPlay(settings, y) ? ' out-of-play' : '')
          + (knowledge === 'unknown' ? ' unknown' : '')
          + (knowledge === 'enemy' ? ' remembered' : ''),
        x: PAD + x * SQUARE,
        y: PAD + y * SQUARE,
        width: SQUARE,
        height: SQUARE,
        rx: 3,
      });
      rect.dataset.x = x;
      rect.dataset.y = y;
      if (settings.onSquare && !isOutOfPlay(settings, y)) {
        rect.addEventListener('click', (event) => {
          event.stopPropagation();
          settings.onSquare(x, y, event);
        });
        rect.style.cursor = 'pointer';
      }
      if (marks.has(`${x},${y}`)) rect.classList.add('fought');
      squares.append(rect);
      const title = svg('title', {});
      title.textContent = describeSquare(board, units, x, y, empty)
        + describeKnowledge(knowledge, known, x, y)
        + describeFight(marks.get(`${x},${y}`))
        + (settings.hint ? '. Arrow keys move about the board' : '');
      rect.append(title);
    }
  }
  root.append(squares);

  // what an army remembered of a square it is not standing on: an enemy met
  // there, with the turn it was met. Drawn as a glyph on the square rather
  // than as a unit, because it is a memory and not a sighting
  if (known) {
    for (const [x, y, turn, attack, health] of known.enemies || []) {
      const group = svg('g', {
        class: 'remembered-enemy',
        transform: `translate(${PAD + x * SQUARE}, ${PAD + y * SQUARE})`,
      });
      const glyph = svg('text', {
        x: SQUARE / 2, y: SQUARE / 2 + 5, 'font-size': 14,
        'text-anchor': 'middle',
      });
      glyph.textContent = ENEMY_SYMBOL;
      group.append(glyph);
      const when = svg('text', {
        class: 'met', x: SQUARE - 4, y: SQUARE - 4, 'font-size': 9,
        'text-anchor': 'end',
      });
      when.textContent = `t${turn}`;
      group.append(when);
      const title = svg('title', {});
      title.textContent = `an enemy met here on turn ${turn}: attack `
        + `${attack}, health ${health} as it was then`;
      group.append(title);
      root.append(group);
    }
  }

  // every flag in the game, on the square it stands on. Drawn for a carrier
  // this seat has never met as well as for one it can see: a flag's square is
  // the one thing shown without contact, and what stands there is not part of
  // it - so this draws a flag and never a unit
  for (const flag of flags) {
    const group = svg('g', {
      class: `flag ${flag.player === settings.mine ? 'mine' : 'theirs'}`,
      transform: `translate(${PAD + flag.x * SQUARE}, ${PAD + flag.y * SQUARE})`,
    });
    const mark = svg('text', {
      class: 'standard',
      x: SQUARE - 9,
      y: 13,
      'font-size': 13,
      'text-anchor': 'middle',
    });
    mark.textContent = '⚑';
    group.append(mark);
    const title = svg('title', {});
    title.textContent = flag.player === settings.mine
      ? `your flag, at (${flag.x}, ${flag.y})`
      : `player ${flag.player}'s flag, at (${flag.x}, ${flag.y}). `
        + 'Destroy what carries it and they are out of the game';
    group.append(title);
    root.append(group);
  }

  // where the turn was fought. Drawn on the square rather than named in a
  // list, because "the contest at (0, 4)" is a coordinate and this is a
  // board: the whole point of having one is that it shows you where
  for (const mark of marks.values()) {
    const group = svg('g', { class: 'clash' });
    const blade = svg('text', {
      class: 'blades',
      x: PAD + mark.x * SQUARE + 9,
      y: PAD + mark.y * SQUARE + SQUARE - 3,
      'font-size': 13,
      'text-anchor': 'middle',
    });
    blade.textContent = mark.fallen.length ? '☠' : '⚔';
    group.append(blade);
    // what it cost this seat, not what was exchanged: a player reads a board
    // for what happened to them
    const cost = mark.taken || mark.dealt;
    if (cost) {
      const damage = svg('text', {
        class: 'damage' + (mark.taken ? ' mine' : ''),
        x: PAD + mark.x * SQUARE + SQUARE - 10,
        y: PAD + mark.y * SQUARE + SQUARE - 3,
        'font-size': 11,
        'text-anchor': 'middle',
      });
      damage.textContent = `-${cost}`;
      group.append(damage);
    }
    const title = svg('title', {});
    title.textContent = describeFight(mark).replace(/^\. /, '');
    group.append(title);
    root.append(group);
  }

  // the cursor, drawn as an outline rather than a fill so it does not depend
  // on colour to be seen
  if (settings.cursor) {
    root.append(svg('rect', {
      class: 'cursor',
      x: PAD + settings.cursor.x * SQUARE + 1.5,
      y: PAD + settings.cursor.y * SQUARE + 1.5,
      width: SQUARE - 3,
      height: SQUARE - 3,
      rx: 3,
    }));
  }

  for (const unit of units) {
    if (unit.x === null || unit.y === null) continue;
    const own = unit.player === mine;
    const group = svg('g', {
      class: `unit ${own ? 'mine' : 'theirs'} player-${unit.player}`
        + (unit.pending ? ' pending' : ''),
      transform: `translate(${PAD + unit.x * SQUARE}, ${PAD + unit.y * SQUARE})`,
    });
    // a unit keeps its element across redraws of the replay by its key, so
    // the browser can animate it from where it was to where it is
    group.dataset.key = `${unit.player}/${unit.name}`;
    // where it stands, said rather than left to be read back out of the
    // transform. The squares under it carry theirs for the same reason
    group.dataset.x = unit.x;
    group.dataset.y = unit.y;
    // an invisible target covering the square. The ring is 23px across on a
    // phone and a finger is about 44: what somebody aims at is the square
    group.append(svg('rect', {
      class: 'hit',
      x: 0, y: 0, width: SQUARE, height: SQUARE,
      fill: 'transparent',
    }));
    group.append(svg('circle', {
      class: 'ring',
      cx: SQUARE / 2,
      cy: SQUARE / 2,
      r: RING,
    }));

    // the energy the unit has left, drawn as an arc round it. Energy is what
    // decides whether a unit can move, whether it can strike, and whether its
    // controller can think - and a spent unit and a fresh one used to be
    // drawn identically.
    //
    // Drawn OUTSIDE the ring rather than along it. The ring says whose the
    // unit is, and an arc painted on the same line hid that
    const power = settings.energyOf ? settings.energyOf(unit) : null;
    if (power && Number.isFinite(power.now) && power.full > 0) {
      const round = 2 * Math.PI * ARC;
      const share = Math.max(0, Math.min(1, power.now / power.full));
      group.append(svg('circle', {
        class: `energy ${band(share)}`,
        cx: SQUARE / 2,
        cy: SQUARE / 2,
        r: ARC,
        // drawn from the top, clockwise, so it reads like a dial rather than
        // starting at three o'clock where SVG would put it
        transform: `rotate(-90 ${SQUARE / 2} ${SQUARE / 2})`,
        'stroke-dasharray': `${round * share} ${round}`,
      }));
    }
    const text = svg('text', {
      x: SQUARE / 2,
      y: SQUARE / 2 + 5,
      'font-size': 14,
    });
    text.textContent = unit.symbol;
    group.append(text);

    // health, as a bar under the ring. A unit one blow from destruction and a
    // unit nobody has touched drew identically, which made the number that
    // decides a fight the one thing the board withheld
    const left = settings.healthOf ? settings.healthOf(unit) : null;
    if (left && Number.isFinite(left.now)) {
      const width = SQUARE - 16;
      const share = left.full ? Math.max(0, Math.min(1, left.now / left.full))
                              : 1;
      group.append(svg('rect', {
        class: 'health-track',
        x: 8, y: 3, width, height: 3, rx: 1.5,
      }));
      group.append(svg('rect', {
        // the same three bands as the energy arc above it, from the same
        // function: a player learns one scale, not two
        class: `health-left ${band(share)}`,
        x: 8, y: 3, width: Math.max(0, width * share), height: 3, rx: 1.5,
      }));
    }

    // the chosen unit is outlined, and dashed as well as coloured, so which it
    // is does not depend on colour alone
    if (selected.has(`${unit.player}/${unit.name}`)
        || (own && selected.has(unit.name))) {
      group.append(svg('rect', {
        class: 'selected',
        x: 2, y: 2, width: SQUARE - 4, height: SQUARE - 4, rx: 3,
      }));
    }
    // a click on a unit chooses it: on the deploy board it is this seat's
    // own and is taken back, and on the replay board it is any unit and its
    // trace is shown. The screen decides which; the board only says which
    // unit was clicked
    if (settings.onUnit && (own || settings.anyUnit)) {
      group.style.cursor = 'pointer';
      group.addEventListener('click', (event) => {
        event.stopPropagation();
        settings.onUnit(unit, event);
      });
    } else if (settings.onSquare) {
      // a unit that is not this seat's own is standing on a square, and the
      // square is what a click on it means. Its own drawing covers the
      // square completely, so without this such a unit swallowed every click
      group.style.cursor = 'pointer';
      group.addEventListener('click', (event) => {
        event.stopPropagation();
        settings.onSquare(unit.x, unit.y, event);
      });
    }
    // and picked up and put down, which is what a person does to a board.
    // Where the drop leads - a square to deploy on, or a refusal - is the
    // screen's to decide, exactly as `onUnit` is. Offered only where the
    // screen offers it, which is the deploy board and nowhere else
    if (settings.onDrop && own) {
      makeDraggable(root, group, unit, settings);
    }
    // what a person gets for hovering: everything the unit is, and how to
    // read more of it
    const title = svg('title', {});
    title.textContent = describeUnit(unit, own, left, settings.hint);
    group.append(title);

    root.append(group);
  }
  return root;
}

// --- picking a unit up
//
// One code path for a mouse, a pen and a finger: pointer events, a capture so
// the gesture survives leaving the square it began in, and a threshold below
// which what happened was a click. HTML5 drag-and-drop would have been less
// code and does not fire for touch on any phone, which is the device this is
// most for.

/**
 * Let one unit be dragged to a square, and tell the screen where it landed.
 *
 * The transform written here during the gesture is the one place in the page
 * that changes the DOM outside `render`, and it is deliberate: re-rendering
 * per pointer move would rebuild the SVG under the pointer, throwing away the
 * element holding the capture and ending the drag on its first movement.
 * Nothing else is written - no state, no command - and the drop goes back
 * through the screen, the contract and a redraw like every other action, so
 * what is finally drawn still comes from the server.
 */
function makeDraggable(root, group, unit, settings) {
  group.classList.add('draggable');
  const home = `translate(${PAD + unit.x * SQUARE}, ${PAD + unit.y * SQUARE})`;
  let gesture = null;

  group.addEventListener('pointerdown', (event) => {
    // the primary button only: a right-click is a menu, not a move
    if (event.button) return;
    event.stopPropagation();
    gesture = { id: event.pointerId, from: at(root, event), moved: false };
    group.setPointerCapture(event.pointerId);
  });

  group.addEventListener('pointermove', (event) => {
    if (!gesture || event.pointerId !== gesture.id) return;
    const here = at(root, event);
    const dx = here.x - gesture.from.x;
    const dy = here.y - gesture.from.y;
    if (!gesture.moved && Math.hypot(dx, dy) < DRAG_THRESHOLD) return;
    gesture.moved = true;
    group.classList.add('dragging');
    group.setAttribute('transform',
      `translate(${PAD + unit.x * SQUARE + dx}, `
      + `${PAD + unit.y * SQUARE + dy})`);
  });

  const drop = (event) => {
    if (!gesture || event.pointerId !== gesture.id) return;
    const moved = gesture.moved;
    const here = at(root, event);
    gesture = null;
    group.classList.remove('dragging');
    // put it back where the view says it is. If the drop is accepted the
    // redraw that follows moves it; if it is refused this is where it belongs
    group.setAttribute('transform', home);
    if (!moved) return;
    // the click the browser fires after a drag would choose the unit as
    // well, so it is swallowed once
    group.addEventListener('click', (click) => {
      click.stopPropagation();
      click.preventDefault();
    }, { capture: true, once: true });
    const x = Math.floor((here.x - PAD) / SQUARE);
    const y = Math.floor((here.y - PAD) / SQUARE);
    settings.onDrop(unit, x, y);
  };
  group.addEventListener('pointerup', drop);
  group.addEventListener('pointercancel', (event) => {
    if (!gesture || event.pointerId !== gesture.id) return;
    gesture = null;
    group.classList.remove('dragging');
    group.setAttribute('transform', home);
  });
}

/**
 * Where a pointer is, in the board's own coordinates.
 *
 * Through the SVG's screen matrix rather than by dividing a bounding
 * rectangle by 44: the board is drawn in a `viewBox` and scaled to fit, so
 * pixels on the glass and squares on the board are not the same size.
 */
function at(root, event) {
  const matrix = root.getScreenCTM();
  if (!matrix) return { x: event.clientX, y: event.clientY };
  const point = root.createSVGPoint();
  point.x = event.clientX;
  point.y = event.clientY;
  const inside = point.matrixTransform(matrix.inverse());
  return { x: inside.x, y: inside.y };
}

/**
 * Whether this row is one the seat being drawn for may not deploy in.
 *
 * `placeable` is the rows the contract says this seat may use, and it is
 * given only while units are being placed. Absent - on the replay board, or
 * in a game whose placement is unrestricted - nothing is greyed.
 */
function isOutOfPlay(settings, y) {
  return Boolean(settings.placeable) && !settings.placeable.includes(y);
}

/**
 * What an army knew of a square, from the record's map: `unknown`, `empty`
 * or `enemy`. A square one of its own units stands on is drawn as the unit
 * and asked about nowhere.
 */
export function knownAt(known, x, y) {
  if ((known.enemies || []).some(([ex, ey]) => ex === x && ey === y)) {
    return 'enemy';
  }
  if ((known.visited || []).some(([vx, vy]) => vx === x && vy === y)) {
    return 'empty';
  }
  return 'unknown';
}

function describeKnowledge(knowledge, known, x, y) {
  if (!knowledge) return '';
  if (knowledge === 'unknown') return '. Unknown to this army';
  if (knowledge === 'empty') {
    const [, , turn] = (known.visited || []).find(
      ([vx, vy]) => vx === x && vy === y);
    return `. Known empty, last stood on by this army on turn ${turn}`;
  }
  return '';
}

/**
 * One unit, said in full: whose it is, what it was built with, what it has
 * left, and how to read more of it.
 *
 * The same sentence for an enemy as for your own, because what you may know
 * about an enemy is decided before the view reaches here.
 */
export function describeUnit(unit, own, left, hint) {
  const full = left && left.full ? ` of ${left.full}` : '';
  const said = [
    `${unit.name} (${unit.type}) — ${own ? 'yours' : 'theirs'}`,
    `attack ${unit.attack}`,
    `health ${unit.health}${full}`,
    `energy ${unit.energy}`,
  ];
  // the one thing about a unit a player cannot read off the drawing, and
  // which used to be a paragraph under the board
  if (unit.pending) {
    said.push('deployed here and not on the field yet: it takes the field '
      + 'when the game is resolved');
  }
  const sentence = said.join(', ');
  if (!hint) return sentence;
  // the hint over a unit in the replay says how to read its trace: a click,
  // or Enter with the cursor over it. Nothing is ordered from the keyboard
  // or anywhere else - orders are the controllers' alone
  return `${sentence}. Click it, or press Enter over it, to read what its `
    + 'controller did this turn.';
}

function describeFight(mark) {
  if (!mark) return '';
  const said = [];
  if (mark.taken) said.push(`${mark.taken} damage taken here this turn`);
  if (mark.dealt) said.push(`${mark.dealt} dealt`);
  if (mark.fallen.length) {
    said.push(`${mark.fallen.join(', ')} destroyed here`);
  }
  if (!said.length) said.push('fought over this turn');
  return `. ${said.join('; ')}`;
}

function describeSquare(board, units, x, y, empty) {
  const here = units.filter((unit) => unit.x === x && unit.y === y);
  if (here.length === 0) return `(${x}, ${y}) empty`;
  return `(${x}, ${y}) ` +
    here.map((unit) => `${unit.name} (${unit.type})`).join(', ');
}

export { SQUARE, PAD, UNKNOWN_SYMBOL, ENEMY_SYMBOL };

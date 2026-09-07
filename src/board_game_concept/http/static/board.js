// The board: one <svg>, squares drawn once, a <g> per unit positioned by
// transform.
//
// Moving a unit between turns is a change of that transform, and the CSS
// transition on it is the whole animation - no timeline, no frame loop, no
// library. `prefers-reduced-motion` turns it off.
//
// This file draws what the view gives it and never decides what to conceal.
// A seat's published view already holds only what that seat may see, so
// everything here has already been filtered where `visibility` filters it -
// and a board that tried to be clever about hiding would be a second opinion
// on a question that already has an answer.

const NS = 'http://www.w3.org/2000/svg';


/**
 * Give a node a click and a double-click that cannot both happen.
 *
 * One gesture, one outcome: a click that turns out to be the first half of a
 * double-click never also does what a single click does.
 */
function makeClickable(node, single, double) {
  let timer = null;
  node.addEventListener('click', (event) => {
    event.stopPropagation();
    // where nothing is waiting for a second click there is nothing to wait
    // for: the deploy board places a unit the moment it is asked, as it
    // always has, and only a board that offers both defers anything
    if (!double) {
      if (single) single(event);
      return;
    }
    if (timer) {
      // the second click of a pair, and the first has not happened yet
      clearTimeout(timer);
      timer = null;
      event.preventDefault();
      double(event);
      return;
    }
    timer = setTimeout(() => { timer = null; if (single) single(event); },
                       CLICK_DELAY);
  });
}
const SQUARE = 44;
const PAD = 6;

// the ring is smaller than the square it stands in, so that an order drawn
// out of it has somewhere to be drawn: a unit that filled its square left
// the arrow saying where it was going crammed against the edge
const RING = SQUARE / 2 - 11;

// how far an order's arrow reaches out of the square, as a share of one
// square. Past the edge on purpose - what it points at is the square it is
// going to, which is the whole of what the arrow is for
const REACH = 0.78;

// how far the pointer travels before a click becomes a drag. Without it every
// tap on a unit is a one-pixel drag, and selecting a unit - the thing done
// most often - stops working
const DRAG_THRESHOLD = 4;

// how far it travels before a press on the board becomes a box. Deliberately
// much further than a drag's: a double-click is two presses in the same place
// by a hand that is not perfectly still, and a box drawn on that jitter took
// the selection away - it caught nothing, and nothing is what it then
// selected - a moment before the second click tried to order it. Half a
// square is a movement somebody meant to make.
//
// In the board's own units, so it is half a square however the board is
// scaled to its pane: `DRAG_THRESHOLD` is four of those, which on a board
// scaled up is less than a pixel of glass.
const BOX_THRESHOLD = SQUARE / 2;

// how long a single click waits to see whether a second is coming. Both mean
// something here - a click chooses and a double-click orders - so the click's
// effect is held for this long and dropped if the second arrives.
//
// The pair is counted here rather than left to the browser's `dblclick`,
// because the first click of a pair redraws the board: it moves the cursor,
// and `render` replaces the whole SVG. The element the browser would have
// fired `dblclick` at is gone by then. Counting the clicks ourselves means
// the redraw simply never happens - the first click's effect is still
// waiting when the second cancels it
const CLICK_DELAY = 350;

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
  return '#';
}

/**
 * Draw a board.
 *
 * `options` carries what the screen knows and the board does not: whose seat
 * this is, which units are selected, where the keyboard cursor is, and what to
 * do when a square is chosen.
 */
export function renderBoard(board, units, options) {
  const settings = options || {};
  const mine = settings.mine;
  // the selection is a set of names, and every one of them is marked. It
  // used to be a single name, and a group drawn with one unit outlined would
  // be a board that disagreed with the order it is about to be given
  const selected = new Set(settings.selected || []);
  const width = board.size_x * SQUARE + PAD * 2;
  const height = board.size_y * SQUARE + PAD * 2;
  // room to begin a box outside the grid. Without it a group standing in a
  // corner cannot be boxed at all: a box has to begin somewhere that is not a
  // unit, and every square around such a group is either a unit or off the
  // board. The margin is drawn on nothing and only ever pressed on
  const grab = settings.onBox ? SQUARE / 2 : 0;

  const root = svg('svg', {
    // a watching session owns none of the units, so "yours and theirs" says
    // nothing to it and every unit was drawn as an enemy. It is told to
    // colour by player instead
    class: 'board' + (settings.watching ? ' watching' : '')
      + (settings.onBox ? ' boxable' : ''),
    viewBox: `${-grab} ${-grab} ${width + grab * 2} ${height + grab * 2}`,
    width: width + grab * 2,
    height: height + grab * 2,
    role: 'grid',
    'aria-label': `board, ${board.size_x} by ${board.size_y}`,
  });

  // the margin, as something a pointer can land on. An `<svg>` element's own
  // background is not reliably a target, and a press that hits nothing starts
  // nothing
  if (grab) {
    root.append(svg('rect', {
      class: 'field',
      x: -grab,
      y: -grab,
      width: width + grab * 2,
      height: height + grab * 2,
      fill: 'transparent',
    }));
  }

  const empty = emptySymbol(board);
  const marks = settings.marks || new Map();
  const flags = (settings.flags || []).filter(
    (flag) => flag.standing && flag.x !== null && flag.y !== null);
  const squares = svg('g', { class: 'squares' });
  for (let y = 0; y < board.size_y; y += 1) {
    for (let x = 0; x < board.size_x; x += 1) {
      const rect = svg('rect', {
        class: 'square'
          + (isReachable(settings, x, y) ? ' reachable' : '')
          + (isOutOfPlay(settings, y) ? ' out-of-play' : ''),
        x: PAD + x * SQUARE,
        y: PAD + y * SQUARE,
        width: SQUARE,
        height: SQUARE,
        rx: 3,
      });
      rect.dataset.x = x;
      rect.dataset.y = y;
      if ((settings.onSquare || settings.onSquareDouble)
          && !isOutOfPlay(settings, y)) {
        makeClickable(
          rect,
          settings.onSquare && ((event) => settings.onSquare(x, y, event)),
          settings.onSquareDouble
            && ((event) => settings.onSquareDouble(x, y, event)));
        rect.style.cursor = 'pointer';
      }
      if (marks.has(`${x},${y}`)) rect.classList.add('fought');
      squares.append(rect);
      const title = svg('title', {});
      title.textContent = describeSquare(board, units, x, y, empty)
        + describeFight(marks.get(`${x},${y}`))
        + (settings.hint ? '. Arrow keys move about the board' : '');
      rect.append(title);
    }
  }
  root.append(squares);

  // a drag that begins on a square rather than on a unit draws a box round
  // the units it crosses. It is put on the squares layer, so which gesture
  // starts is decided by what is under the pointer when it goes down -
  // exactly as it is on a table
  if (settings.onBox) makeBoxable(root, board, settings);

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

  // where the last turn was fought. Drawn on the square rather than named in
  // a list, because "the contest at (0, 4)" is a coordinate and this is a
  // board: the whole point of having one is that it shows you where
  for (const mark of marks.values()) {
    const group = svg('g', { class: 'clash' });
    // bottom left, and the damage bottom right: the middle of the bottom
    // edge belongs to the order arrow, and the top edge to the health bar
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

    // the energy the unit has left, drawn as the share of its own ring it
    // can still pay for. Energy is what decides whether a unit can move,
    // whether it can strike, and whether it is inert - the thing to know
    // before ordering it - and it was a number in a table while the board a
    // player is looking at drew a spent unit and a fresh one identically
    const power = settings.energyOf ? settings.energyOf(unit) : null;
    if (power && Number.isFinite(power.now) && power.full > 0) {
      const round = 2 * Math.PI * RING;
      const share = Math.max(0, Math.min(1, power.now / power.full));
      group.append(svg('circle', {
        class: 'energy' + (share <= 0.25 ? ' spent' : ''),
        cx: SQUARE / 2,
        cy: SQUARE / 2,
        r: RING,
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
    // decides whether to fight or fall back the one thing the board withheld
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
        class: 'health-left' + (share <= 0.25 ? ' critical' : ''),
        x: 8, y: 3, width: Math.max(0, width * share), height: 3, rx: 1.5,
      }));
    }

    if (own && selected.has(unit.name)) {
      group.append(svg('rect', {
        class: 'selected',
        x: 2, y: 2, width: SQUARE - 4, height: SQUARE - 4, rx: 3,
      }));
    }
    if ((settings.onUnit || settings.onUnitDouble) && own) {
      group.style.cursor = 'pointer';
      // the event goes with it: whether shift was held is the screen's to
      // interpret, and the board goes on knowing nothing about what a
      // selection is
      makeClickable(
        group,
        settings.onUnit && ((event) => settings.onUnit(unit, event)),
        settings.onUnitDouble && ((event) => settings.onUnitDouble(unit, event)));
    } else if (settings.onSquare || settings.onSquareDouble) {
      // a unit that is not this seat's own is standing on a square, and the
      // square is what a click on it means. Its own drawing covers the
      // square completely, so without this an enemy swallowed every click
      // that landed on it - and moving onto an enemy is how you attack, so
      // the one square a player most wants to order a unit onto was the one
      // square they could not name
      group.style.cursor = 'pointer';
      makeClickable(
        group,
        settings.onSquare
          && ((event) => settings.onSquare(unit.x, unit.y, event)),
        settings.onSquareDouble
          && ((event) => settings.onSquareDouble(unit.x, unit.y, event)));
    }
    // and picked up and put down, which is what a person does to a board.
    // Where the drop leads - a square to deploy on, a square to move to, or
    // a refusal - is the screen's to decide, exactly as `onUnit` is
    if (settings.onDrop && own) {
      makeDraggable(root, group, unit, settings);
    }
    // what a person gets for hovering: everything the unit is, and - for
    // one of theirs - how to order it. The keyboard is faster than the
    // mouse here and nothing said so anywhere near the board
    const title = svg('title', {});
    title.textContent = describeUnit(unit, own, left, settings.hint);
    group.append(title);

    // an order in flight is drawn as an arrow out of the square and into the
    // one it is headed for, so what a unit has been told to do is legible
    // from across a table rather than being a glyph the size of a full stop
    if (own && unit.direction) {
      const heading = HEADINGS[unit.direction];
      if (heading) group.append(orderArrow(heading));
    }
    root.append(group);
  }
  return root;
}

// --- drawing a box round several units
//
// The same pointer-event machinery as the drag below, and deliberately the
// same threshold: a press and release that never travelled is a click, and
// the click listener already on the square deals with it.

/**
 * Let a drag across empty squares select the units it encloses.
 *
 * The rectangle is written into the DOM during the gesture, which is the same
 * exception `makeDraggable` makes and for the same reason: re-rendering per
 * pointer move would rebuild the SVG under the pointer and throw away the
 * element holding the capture.
 *
 * Nothing here decides what a selection is. The two corners go back to the
 * screen in board coordinates, and which units that catches - whose they are,
 * whether they are standing - is the screen's to answer.
 */
function makeBoxable(root, board, settings) {
  let gesture = null;
  let box = null;
  // the second finger, where there is one. A one-finger drag on a phone is a
  // page scroll and stays one - the stylesheet leaves panning to the browser
  // - so the box a finger draws is the rectangle between two of them
  let second = null;

  // a corner of the box, as a square. A press in the margin is outside the
  // grid on purpose, so it is clamped to the edge square rather than refused:
  // what somebody means by starting a box off the corner of the board is the
  // corner of the board
  const corner = (point) => ({
    x: Math.min(Math.max(Math.floor((point.x - PAD) / SQUARE), 0),
                board.size_x - 1),
    y: Math.min(Math.max(Math.floor((point.y - PAD) / SQUARE), 0),
                board.size_y - 1),
  });

  root.addEventListener('pointerdown', (event) => {
    if (event.button) return;
    // a second finger while a first is down: the two are opposite corners of
    // the box from here on, and the drag threshold does not apply - putting
    // two fingers down is already deliberate
    if (gesture && event.pointerId !== gesture.id) {
      second = { id: event.pointerId, at: at(root, event) };
      gesture.moved = true;
      root.setPointerCapture(event.pointerId);
      draw(gesture.from, second.at);
      return;
    }
    // and no pointer capture yet. A captured pointer makes the browser
    // dispatch the click at the element holding the capture, so capturing
    // here delivered every click on the board to the <svg> itself and the
    // square under the pointer never heard it - which is why a double-click
    // ordered nothing anywhere except on a unit, whose own pointerdown stops
    // this one from running at all. It is taken below, once the gesture has
    // travelled far enough to be a box and there is no click left to lose
    gesture = { id: event.pointerId, from: at(root, event), moved: false };
  });

  // where the far corner of the box is: the second finger if there is one,
  // and otherwise wherever the one pointer has reached
  const opposite = (here) => (second ? second.at : here);

  const draw = (from, to) => {
    if (!box) {
      box = svg('rect', { class: 'selection-box', rx: 2 });
      root.append(box);
    }
    box.setAttribute('x', Math.min(from.x, to.x));
    box.setAttribute('y', Math.min(from.y, to.y));
    box.setAttribute('width', Math.abs(to.x - from.x));
    box.setAttribute('height', Math.abs(to.y - from.y));
  };

  root.addEventListener('pointermove', (event) => {
    if (!gesture) return;
    if (second && event.pointerId === second.id) {
      second.at = at(root, event);
      draw(gesture.from, second.at);
      return;
    }
    if (event.pointerId !== gesture.id) return;
    const here = at(root, event);
    // the first finger may move too, and where a second is down it is a
    // corner rather than a drag: no threshold, the box simply follows
    if (second) {
      gesture.from = here;
      draw(here, second.at);
      return;
    }
    if (!gesture.moved
        && Math.hypot(here.x - gesture.from.x, here.y - gesture.from.y)
           < BOX_THRESHOLD) return;
    gesture.moved = true;
    // now it is a box, so the gesture is followed off the square it began on
    root.setPointerCapture(event.pointerId);
    draw(gesture.from, here);
  });

  const done = (event) => {
    if (!gesture) return;
    // either finger ending the gesture takes the box: a player lifting one
    // of two has finished choosing, and which one they lifted is not a
    // distinction they were making
    if (event.pointerId !== gesture.id
        && !(second && event.pointerId === second.id)) return;
    const moved = gesture.moved;
    const from = corner(gesture.from);
    const to = corner(
      event.pointerId === gesture.id ? opposite(at(root, event))
                                     : (second ? second.at : at(root, event)));
    gesture = null;
    second = null;
    if (box) { box.remove(); box = null; }
    // a press that never travelled is a click, and the square's own click
    // listener has already dealt with it
    if (!moved) return;
    // the click the browser fires after a drag would move the cursor to
    // wherever the box happened to end, so it is swallowed once
    root.addEventListener('click', (click) => {
      click.stopPropagation();
      click.preventDefault();
    }, { capture: true, once: true });
    settings.onBox(from.x, from.y, to.x, to.y);
  };
  root.addEventListener('pointerup', done);
  // a one-finger drag the browser claims for panning arrives here, which is
  // what keeps the page scrolling and the box from fighting it
  root.addEventListener('pointercancel', (event) => {
    if (!gesture) return;
    if (second && event.pointerId === second.id) { second = null; return; }
    if (event.pointerId !== gesture.id) return;
    gesture = null;
    second = null;
    if (box) { box.remove(); box = null; }
  });
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
    // and never a selection box as well: a press that lands on a unit is
    // picking that unit up, whatever is drawn under it
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
    // the click the browser fires after a drag would select the unit or
    // order it a second time, so it is swallowed once
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

// which way each order points, in board coordinates
const HEADINGS = {
  north: { dx: 0, dy: -1 }, east: { dx: 1, dy: 0 },
  south: { dx: 0, dy: 1 }, west: { dx: -1, dy: 0 },
};

/**
 * The arrow drawn for a unit under orders.
 *
 * A line out of the ring with a head on it, in the square's own coordinates
 * - the unit's group is already translated, so this is drawn as though the
 * unit were at the origin.
 */
function orderArrow({ dx, dy }) {
  const middle = SQUARE / 2;
  const from = { x: middle + dx * (RING + 2), y: middle + dy * (RING + 2) };
  const to = { x: middle + dx * SQUARE * REACH,
               y: middle + dy * SQUARE * REACH };
  const group = svg('g', { class: 'order' });
  group.append(svg('line', {
    class: 'shaft',
    x1: from.x, y1: from.y,
    // stops short of the point, so the head is a head rather than a blob
    x2: to.x - dx * 7, y2: to.y - dy * 7,
  }));
  // the head, as a triangle across the direction of travel
  const across = { x: -dy, y: dx };
  const head = [
    `${to.x},${to.y}`,
    `${to.x - dx * 9 + across.x * 5},${to.y - dy * 9 + across.y * 5}`,
    `${to.x - dx * 9 - across.x * 5},${to.y - dy * 9 - across.y * 5}`,
  ].join(' ');
  group.append(svg('polygon', { class: 'head', points: head }));
  return group;
}

/**
 * Whether this row is one the seat being drawn for may not deploy in.
 *
 * `placeable` is the rows the contract says this seat may use, and it is
 * given only while units are being placed. Absent - on the play board, or in
 * a game whose placement is unrestricted - nothing is greyed.
 */
function isOutOfPlay(settings, y) {
  return Boolean(settings.placeable) && !settings.placeable.includes(y);
}

function isReachable(settings, x, y) {
  if (!settings.reachable) return false;
  return settings.reachable.some((square) => square.x === x && square.y === y);
}

/**
 * One unit, said in full: whose it is, what it was built with, what it has
 * left, and what it has been told to do.
 *
 * The same sentence for an enemy as for your own, because what you may know
 * about an enemy is decided before the view reaches here - if it is on this
 * board you have met it, and its statistics are yours to read.
 */
export function describeUnit(unit, own, left, hint) {
  const full = left && left.full ? ` of ${left.full}` : '';
  const said = [
    `${unit.name} (${unit.type}) — ${own ? 'yours' : 'theirs'}`,
    `attack ${unit.attack}`,
    `health ${unit.health}${full}`,
    `energy ${unit.energy}`,
  ];
  // the two things about a unit a player cannot read off the drawing, and
  // which used to be paragraphs under the board
  if (unit.pending) {
    said.push('deployed here and not on the field yet: it takes the field '
      + 'when the first turn resolves');
  }
  if (unit.direction) {
    said.push(unit.committed
      ? `ordered ${unit.direction}, committed: it cannot be changed until the `
        + 'turn resolves'
      : `ordered ${unit.direction}`);
  }
  const sentence = said.join(', ');
  if (!own || !hint) return sentence;
  return `${sentence}. Click it or press Enter over it, then an arrow key `
    + 'to order it that way. Shift-click adds it to a group, and a box drawn '
    + 'across the board takes every unit in it. Double-click to one side of '
    + 'what is selected to send it that way — a direction, not a square, and '
    + 'it acts on the selection whatever is standing there — and double-click '
    + 'the selection itself to take its orders back.';
}

function describeFight(mark) {
  if (!mark) return '';
  const said = [];
  if (mark.taken) said.push(`${mark.taken} damage taken here last turn`);
  if (mark.dealt) said.push(`${mark.dealt} dealt`);
  if (mark.fallen.length) {
    said.push(`${mark.fallen.join(', ')} destroyed here`);
  }
  if (!said.length) said.push('fought over last turn');
  return `. ${said.join('; ')}`;
}

function describeSquare(board, units, x, y, empty) {
  const here = units.filter((unit) => unit.x === x && unit.y === y);
  if (here.length === 0) return `(${x}, ${y}) empty`;
  return `(${x}, ${y}) ` +
    here.map((unit) => `${unit.name} (${unit.type})`).join(', ');
}

export { SQUARE, PAD };

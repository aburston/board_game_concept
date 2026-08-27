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
const SQUARE = 44;
const PAD = 6;

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
  // is read off the rows rather than assumed here
  for (const row of board.rows) {
    for (const cell of row) if (cell) return cell;
  }
  return '#';
}

/**
 * Draw a board.
 *
 * `options` carries what the screen knows and the board does not: whose seat
 * this is, which unit is selected, where the keyboard cursor is, and what to
 * do when a square is chosen.
 */
export function renderBoard(board, units, options) {
  const settings = options || {};
  const mine = settings.mine;
  const width = board.size_x * SQUARE + PAD * 2;
  const height = board.size_y * SQUARE + PAD * 2;

  const root = svg('svg', {
    class: 'board',
    viewBox: `0 0 ${width} ${height}`,
    width,
    height,
    role: 'grid',
    'aria-label': `board, ${board.size_x} by ${board.size_y}`,
  });

  const empty = emptySymbol(board);
  const squares = svg('g', {});
  for (let y = 0; y < board.size_y; y += 1) {
    for (let x = 0; x < board.size_x; x += 1) {
      const rect = svg('rect', {
        class: 'square' + (isReachable(settings, x, y) ? ' reachable' : ''),
        x: PAD + x * SQUARE,
        y: PAD + y * SQUARE,
        width: SQUARE,
        height: SQUARE,
        rx: 3,
      });
      rect.dataset.x = x;
      rect.dataset.y = y;
      if (settings.onSquare) {
        rect.addEventListener('click', () => settings.onSquare(x, y));
        rect.style.cursor = 'pointer';
      }
      squares.append(rect);
      const title = svg('title', {});
      title.textContent = describeSquare(board, units, x, y, empty);
      rect.append(title);
    }
  }
  root.append(squares);

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
      class: `unit ${own ? 'mine' : 'theirs'}`,
      transform: `translate(${PAD + unit.x * SQUARE}, ${PAD + unit.y * SQUARE})`,
    });
    group.append(svg('circle', {
      class: 'ring',
      cx: SQUARE / 2,
      cy: SQUARE / 2,
      r: SQUARE / 2 - 7,
    }));
    const text = svg('text', {
      x: SQUARE / 2,
      y: SQUARE / 2 + 6,
      'font-size': 18,
    });
    text.textContent = unit.symbol;
    group.append(text);

    if (own && unit.name === settings.selected) {
      group.append(svg('rect', {
        class: 'selected',
        x: 2, y: 2, width: SQUARE - 4, height: SQUARE - 4, rx: 3,
      }));
    }
    if (settings.onUnit && own) {
      group.style.cursor = 'pointer';
      group.addEventListener('click', (event) => {
        event.stopPropagation();
        settings.onUnit(unit);
      });
    }
    const title = svg('title', {});
    title.textContent =
      `${unit.name} (${unit.type}) — ${own ? 'yours' : 'theirs'}, ` +
      `attack ${unit.attack}, health ${unit.health}, energy ${unit.energy}`;
    group.append(title);

    // an order in flight is drawn as an arrow out of the square, so what a
    // unit has been told to do is visible on the board and not only in a list
    if (own && unit.direction) {
      const arrow = svg('text', {
        class: 'arrow',
        x: SQUARE / 2,
        y: SQUARE - 3,
        'font-size': 12,
        'text-anchor': 'middle',
      });
      arrow.textContent = { north: '↑', east: '→', south: '↓',
                            west: '←' }[unit.direction] || '';
      group.append(arrow);
    }
    root.append(group);
  }
  return root;
}

function isReachable(settings, x, y) {
  if (!settings.reachable) return false;
  return settings.reachable.some((square) => square.x === x && square.y === y);
}

function describeSquare(board, units, x, y, empty) {
  const here = units.filter((unit) => unit.x === x && unit.y === y);
  if (here.length === 0) return `(${x}, ${y}) empty`;
  return `(${x}, ${y}) ` +
    here.map((unit) => `${unit.name} (${unit.type})`).join(', ');
}

export { SQUARE, PAD };

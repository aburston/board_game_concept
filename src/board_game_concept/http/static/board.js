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
  const marks = settings.marks || new Map();
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
      if (marks.has(`${x},${y}`)) rect.classList.add('fought');
      squares.append(rect);
      const title = svg('title', {});
      title.textContent = describeSquare(board, units, x, y, empty)
        + describeFight(marks.get(`${x},${y}`));
      rect.append(title);
    }
  }
  root.append(squares);

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
      class: `unit ${own ? 'mine' : 'theirs'}`,
      transform: `translate(${PAD + unit.x * SQUARE}, ${PAD + unit.y * SQUARE})`,
    });
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
      r: SQUARE / 2 - 7,
    }));
    const text = svg('text', {
      x: SQUARE / 2,
      y: SQUARE / 2 + 6,
      'font-size': 18,
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
      `attack ${unit.attack}, health ${unit.health}` +
      (left && left.full ? ` of ${left.full}` : '') +
      `, energy ${unit.energy}`;
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

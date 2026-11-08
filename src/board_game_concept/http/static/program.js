// A program's listing, worked out as it is typed.
//
// The one parser there is lives on the server, and it has the last word on
// whether a program is accepted. What this does is the half of that a person
// wants to see while typing: each line's tick cost from the tariff the server
// exports, and a mark on a line whose instruction the set does not have, so
// a mistyped mnemonic is seen where it stands rather than reported afterwards.
//
// Pure, and reads nothing but its arguments, so it can be run outside a
// browser against the tariff and held to the server's own listing.

/**
 * Each source line with the ticks it costs.
 *
 * `tariff` is what `/_/program` answers: `{ticks, ticks_per_compute, ...}`.
 * Without one - the server not yet asked - every line costs nothing and
 * nothing is marked; the server's check still runs.
 *
 * A line is a comment from `;` on, a label is a word ending in `:` before an
 * instruction, and operands are separated by spaces or commas, exactly as
 * `domain/program.py` reads them. A blank line, a comment or a bare label
 * costs nothing and is listed with no ticks.
 */
export function listing(text, tariff) {
  const ticks = (tariff && tariff.ticks) || null;
  const made = [];
  const lines = String(text || '').split('\n');
  // a text that ends in a newline has no line after it, as the server's
  // own `splitlines` reads it
  if (lines.length > 1 && lines[lines.length - 1] === '') lines.pop();
  lines.forEach((raw, index) => {
    const number = index + 1;
    let line = raw.split(';', 1)[0].trim();
    const labelled = /^([A-Za-z_][\w-]*):\s*(.*)$/.exec(line);
    if (labelled) line = labelled[2].trim();
    if (!line) {
      made.push({ line: number, text: raw, ticks: null, error: null });
      return;
    }
    const parts = line.split(/[\s,]+/).filter(Boolean);
    const op = parts[0].toUpperCase();
    if (!ticks) {
      made.push({ line: number, text: raw, ticks: null, error: null });
      return;
    }
    if (!(op in ticks)) {
      made.push({ line: number, text: raw, ticks: null,
                  error: `${op} is not an instruction` });
      return;
    }
    made.push({ line: number, text: raw, ticks: ticks[op], error: null });
  });
  return made;
}

/** What a straight run of the listed program costs. */
export function totalTicks(lines) {
  return lines.reduce((sum, line) => sum + (line.ticks || 0), 0);
}

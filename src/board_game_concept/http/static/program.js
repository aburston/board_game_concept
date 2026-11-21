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
  const macros = definedNames(text, tariff);
  const made = [];
  const lines = String(text || '').split('\n');
  // a text that ends in a newline has no line after it, as the server's
  // own `splitlines` reads it
  if (lines.length > 1 && lines[lines.length - 1] === '') lines.pop();
  let continuing = false;
  lines.forEach((raw, index) => {
    const number = index + 1;
    let line = raw.split(';', 1)[0].trim();
    // a directive, or a line continuing one with a trailing backslash,
    // costs nothing: the preprocessor reads it and the machine never does
    if (continuing || line.startsWith('#')) {
      continuing = line.endsWith('\\');
      made.push({ line: number, text: raw, ticks: null, error: null });
      return;
    }
    const labelled = /^([A-Za-z_][\w-]*):\s*(.*)$/.exec(line);
    if (labelled) line = labelled[2].trim();
    if (!line) {
      made.push({ line: number, text: raw, ticks: null, error: null });
      return;
    }
    const parts = line.split(/[\s,(]+/).filter(Boolean);
    const op = parts[0].toUpperCase();
    if (!ticks) {
      made.push({ line: number, text: raw, ticks: null, error: null });
      return;
    }
    if (macros.has(parts[0])) {
      // a macro the text or a header defines: what it costs is what it
      // expands to, which only the server's check knows
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

/**
 * The names `#define`d in a text and in every header the text includes,
 * so the listing knows which first words are macros rather than mistakes.
 */
export function definedNames(text, tariff) {
  const names = new Set();
  const headers = (tariff && tariff.headers) || {};
  const collect = (source) => {
    for (const raw of String(source || '').split('\n')) {
      const found = /^\s*#\s*define\s+([A-Za-z_]\w*)/.exec(raw);
      if (found) names.add(found[1]);
      const included = /^\s*#\s*include\s*<([\w.]+)>/.exec(raw);
      if (included && included[1] in headers) collect(headers[included[1]]);
    }
  };
  collect(text);
  return names;
}

/** What a straight run of the listed program costs. */
export function totalTicks(lines) {
  return lines.reduce((sum, line) => sum + (line.ticks || 0), 0);
}

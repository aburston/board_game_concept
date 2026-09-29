# Design

## Context

See `proposal.md` - Why. The harness in `matches/arena.py` and the nineteen
bots under `matches/bots/` were written between 25 and 26 August against a
game that has since changed in every part a doctrine reasons about:

| What the bots and harness assume | What the game does now |
|---|---|
| `set board 10 10`; a house split refereed by `vet()` | An 8 x 8 board by default (**R2.1**); halves the game enforces and publishes, rows 0-3 and 4-7 (**R2.6a**) |
| `add player <n> 200`; a seat opens empty | 250 points by default (**R2.3.1**); a seat opens holding the catalogue and sixteen units, flag on `keep1`, 242 points spent (**R2.13**) |
| A fight is rounds until one side dies; kills are `ceil(h / a)` rounds in one turn | One exchange a turn (**R5.2**); a kill this turn needs the strikes landing in it to reach the health (**R5.11**) |
| The enemy is found only by walking into it | Both flag squares are published every turn to everyone (**R6.5**) |
| A player is out when nothing with attack stands | Out when nothing could act, or when the flag falls (**R7.1**, **R7.1a**); eliminated seats' units stay as terrain (**R7.1b**) |
| An undecided contest may leave units sharing a square | Never: a forced-back unit crashes into whatever is behind it (**R5.8a**) |
| `venv/bin/bgcclient` exists | Not in every checkout; the tests launch roles with `sys.executable -m` |
| `show board/units/players/types json` is the whole view | `show flags json` and `show placement json` exist and a player is entitled to both |

Constraints that do not move: a bot is given only its own seat's view; every
order goes through a real prompt; nothing in resolution is random, and nothing
in a doctrine may be either; `src/` is not changed by this work.

## Goals / Non-Goals

**Goals:**
- Twenty games that are evidence about the game as it stands, on the board
  and budget a person gets by default, readable beside the earlier series.
- A harness that will still be right after the next rule change, because it
  takes the board, budget, halves, army and elimination from the game rather
  than restating them.
- Doctrines whose arithmetic is the current combat's, split so that the stock
  army is tested both as it is given and against what a player might build
  instead.
- A record of each game that lets a sentence in the write-up be checked.

**Non-Goals:**
- Changing any rule. Q2 (identical units) and anything the series turns up
  are written down as findings; a rule change is its own change.
- Playing over HTTP. The local flow needs no account and the rules are the
  same; a scripted role against a server would need a token per seat for no
  gain in evidence.
- Keeping the old doctrines runnable. Their write-ups stay as history; the
  code is deleted rather than carried as dead weight nobody can play.
- A browser, a tournament runner, or an Elo table. One script plays one game;
  a shell loop plays the series, as before.
- Making the games a test. They take minutes and their outcomes are the
  question, not the answer; `pytest` holds the harness's boundary, not the
  results.

## Decisions

### 1. The harness asks the game for everything it used to state

`Match.create` sends `add player 1`, `add player 2`, `commit` and nothing else.
No `set board`, no budget, no `--no-split`, no `vet()`. The board size is read
from `show board json`, the halves from `show placement json`, the budget from
`show players json`, and what a seat starts with from `show units json` and
`show types json` in the setup view. The only knob left is `--max-turns`.

*Alternative:* keep the knobs and default them to the game's defaults. Rejected
because a knob is a second statement of a default, and the whole reason this
series is needed is that the last five restated defaults the game then
changed. A future series that wants a different board is a harness change,
which is the right cost.

*Found in implementation:* `bgcserver -g <n>` on a number nobody has created
opens an unsized game, and its `commit` is refused with "the board size is
too small (0, 0)". The default board of `default-army` is given by the
registry's `create`, which is what the lobby calls. The harness creates its
game through that same call before launching the server - the one place it
touches the service layer, and for creation only, never to place, order,
read or resolve. Typing `set board 8 8` instead would restate the default
this decision refuses to restate. The difference between the two ways of
starting a game is recorded in `SPEC_COVERAGE.md` as a divergence.

### 2. Roles launch through the running interpreter

`[sys.executable, '-m', 'board_game_concept.cli.bgcclient', gameno, player]`
and the same for the server and observer, as `tests/test_server_client_integration.py`
does. `ENV` keeps `BOARD_GAME_BACKEND=sqlite`, `BOARD_GAME_NO_REDIRECT=1` and
`PYTHONUNBUFFERED=1`; the local flow needs no account (**README**, "Playing
locally needs no account at all"), so no token is involved.

*Alternative:* the console scripts on `$PATH`. Rejected: they are wherever the
person installed them, and the `venv/bin` guess is what stopped the old
harness running in a fresh checkout.

### 3. Setup is a conversation with a seeded seat

`Bot.setup(view)` is handed the seat as it opens - sixteen units standing,
eight types, `left` in the players subject, the flag on `keep1` in the flags
subject - and returns a list of commands. A doctrine that keeps the army
returns `[]`. One that rebuilds returns `remove unit ...` lines first, then
`add type`, `add unit` and `set flag`; the base class provides `take_back_all`
and `deploy(army)` so a doctrine states its army as data, as before, in
`(type, symbol, attack, health, energy, [(x, depth)])` rows with depth counted
from its own edge and the row worked out from the placement subject.

A commit the client refuses - no flag, nothing deployed, a clash - is a
doctrine bug. The harness logs the refusal, writes the game's log with the
outcome `not played: <reason>` and exits non-zero. It does not repair the
setup or retry, because a series in which the harness quietly edits an army is
not evidence about that army.

*Alternative:* the harness could `set flag` on the doctrine's behalf when it
forgot. Rejected for the same reason: what carries the flag is the most
consequential choice a doctrine makes.

### 4. The view grows two subjects and keeps its boundary

`read_view` types six `show ... json` commands rather than four, adding
`flags` and `placement`, and reads six documents back. `flags` gives the bot
what **R6.5** gives a person: both squares and whose each is, and `fallen`
where a carrier is gone. Nothing else is added. `common.py` gains
`my_flag(view)`, `enemy_flags(view)`, `rows(view)` (from placement) and
`left(view)` (from players). The observer is still opened only for the log,
after both seats have ordered.

### 5. Elimination is read from `status`, not counted

`Match.record` keeps printing an in-play count per seat for the reader,
counting standing units whose type has energy (**R7.1**), but the judgement
of who is in the game comes from `show players json`: `status` is
`eliminated` or `active`, and the client prints `game over: ...` when the
game is decided. The harness stops when either client prints the outcome
line, as now, and additionally logs the turn on which a seat's `status`
changed, so a flag fall (**R7.1a**) is visible in the log even in a
three-seat game where the outcome comes later.

### 6. Combat arithmetic in the doctrines is the one-strike rule's

The number a doctrine reasons with is no longer "rounds to kill" but **strikes
landing in one exchange**: a unit of health `h` dies this turn only if the
attacks landing on it in this exchange sum to `h` or more (**R5.11**). So the
two ways to kill in a turn are one big attack (a Lance's 8, a custom 10) or
several units arriving in the same square at once (three Runners at 2 land 6
on a Line of 6). `common.py` gains `lethal(attackers, target)` and the
`resolve` helper gains a mode that lets several of a bot's own units be
ordered into one *enemy-held* square (they fight together; **R5.7** friendly
fire applies only if they end up sharing, which **R5.8a** forbids - the
survivors fall back). Ordering two own units into one *empty* square is still
passed over, as now.

### 7. Two doctrine families, and a fixed draw of twenty games

**Stock** doctrines return `[]` from `setup` and differ in `orders`:

- **Garrison** - nobody moves; strikes only what walks in. The control: a
  seat that plays the army exactly as handed and does nothing with it.
- **Advance** - the front rank (Pawns and Heavies; the walls cannot) steps
  south or north as a line, resting when its fare would take it below its
  attack; the back rank holds; every contact is pressed next turn.
- **Flag Hunt** - everything but the Keeps and Walls goes for the enemy flag
  square, which is published from turn 1, by the shortest route it can find
  round its own units. *Revised in implementation:* the first version sent
  only the Runners and Lines with the Heavies following, and in game 203
  the Runners and Lines never left the back rank - the stock array boxes
  the back rank in until the front rank moves, and a step that merely
  shortens the distance is a step into a unit of your own. The hunters were
  given a route search round their own units (`path_step`), the Pawns and
  Scouts were sent too, and the eight games Flag Hunt is in were replayed
  before the write-up; the first versions' logs were discarded, since a
  doctrine that could not do what its docstring says is not evidence about
  that doctrine.
- **Screen** - the Scouts (attack 0, fare 1, twelve energy) walk to stand in
  front of the Keeps and the enemy's line of approach, so that whatever comes
  for the flag has to spend a strike on a body that costs 14 points; the rest
  play Advance.

**Rebuilt** doctrines take the army back and deploy their own within 250:

- **Lancers** - eleven Lances (8/2/10, fare 1, 20 points) and a Keep for the
  flag: 236 points. Every strike kills anything of health 8 or less; every
  Lance dies to any strike of 2.
- **Heavies** - seven Heavies (5/10/15, fare 3, 30 points), a Keep and a
  Runner: 242 points. Nothing in the stock army kills a Heavy in one exchange
  short of two Lances arriving together.
- **Runners** - fourteen Runners (2/4/10, fare 1, 16 points) and a Keep: 240
  points. Cheap, fast, and three on one square kill a Line.
- **Bulwark** - eight Walls across the row nearest the frontier, four Heavies
  behind them, a Keep, a Runner and a Scout: 246 points. The wall line has to
  be broken, and each Wall takes a Heavy two turns.
- **Executioner** - a custom type, attack 10, health 4, energy 12 (26 points,
  fare 1): nine of them and a Keep, 250 points exactly. Kills anything on the
  board in one strike; dies to a Runner's 2 in two.
- **Fugitive** - the flag on a Runner rather than a Keep, kept moving at the
  back edge; the rest of the 250 in Lances. Tests whether a visible flag that
  can run is a flag that can be taken.

The draw: each stock doctrine against Garrison (4 games, is the stock army
safe to leave alone), Flag Hunt against each rebuilt doctrine (6 games, what
beats a player who plays what they were given), the six rebuilt doctrines in
a partial round robin (8 games: Lancers-Heavies, Lancers-Runners,
Lancers-Bulwark, Heavies-Runners, Heavies-Bulwark, Runners-Bulwark,
Executioner-Lancers, Fugitive-Executioner), and Flag Hunt against itself and
Advance against itself as mirror controls (2 games). Twenty games, numbered
201-220. The draw is fixed before the first game is played, and every game is
played once: the earlier series' habit of replaying pairings with revised
doctrines is dropped, because it made "20 games" mean 40 and the write-up
had to explain which was which.

*Alternative:* carry the old doctrine names (Swarm, Grinder, Turtle) with new
armies. Rejected: a reader of `RESULTS-QUARTER-FARE.md` who sees "Swarm" in
the new table would assume the same army.

### 8. What the write-up carries

`matches/RESULTS-DEFAULT-BOARD.md` has the structure of `RESULTS-QUARTER-FARE.md`:
what was played (commit, board, budget, halves, army, turn cap, the rules
that changed since 181-200 in a table), the results table (pairing, result,
turn, units in play start and end, flags standing), what decided the decided
games, what the stock army did in each of its four games, what the series
says about Q2 and about the flag, and what it does not show. Every claim about
a turn names the game and turn number so it can be found in the log. The
three write-ups without a superseded banner - `RESULTS-REST-AND-WALLS.md`,
`RESULTS-MOVE-COSTS-HEALTH.md`, `RESULTS-QUARTER-FARE.md` - and the two
commentaries get one, in the words `RESULTS-FRONTIER.md` already uses.

### 9. The harness has tests; the games are not tests

`tests/test_match_harness.py` imports `matches/arena.py` and `matches/bots/`
by path and holds, without launching a game: `json_docs` on a transcript
holding six documents; the view assembled from canned answers carrying
`flags` and `placement`; that a stock doctrine returns `[]`; that each rebuilt
doctrine's stated army costs at most 250, fits its half of an 8 x 8 board,
names one flag carrier, and defines no type the game would refuse (checked
through `UnitType`, which is the game's own rule); that `resolve` never
orders two own units into one empty square and never orders a unit it cannot
pay for; and that every doctrine's `orders` is deterministic across two calls
on the same view. One further test, marked `slow`, plays Garrison against
Garrison for two turns through the real roles and asserts the seat committed
the stock army as given and both seats are `active` afterwards - the harness
smoke test the old arena never had.

## Risks / Trade-offs

- [Twenty games on the default board may all be decided by turn 10, or none
  may be] → Either is a finding; the write-up says which and why. The turn
  cap stays at 60 for comparability with the earlier series.
- [A doctrine's setup is refused for a reason not foreseen, such as a
  redesigned type the game rejects] → The static tests in decision 9 check
  every army against the game's own `UnitType` and `budget` before a game is
  played; a refusal at the prompt still ends the game as `not played` rather
  than silently, so it cannot masquerade as a result.
- [The harness's `wait_for` strings drift from what the client prints] → The
  strings are read from `cli/bgcclient.py` and `cli/session.py` at the time
  of writing and the slow smoke test exercises the commit barrier end to
  end; a later change to the client's wording fails that test.
- [Runtime: twenty games of up to sixty turns, six `show` round trips per
  seat per turn] → Roughly what series 181-200 cost; games are played from a
  shell loop and each writes its own log, so a series can be resumed from
  the last game that finished.
- [Deleting nineteen bots loses doctrines somebody may want to compare
  against] → They are in git history and described in the five write-ups;
  none of them could be played against the current game without being
  rewritten anyway.
- [The stock army might be so strong, or so weak, that the rebuilt games say
  nothing about doctrine] → The four Garrison games are there to show what
  the stock army does when nobody plays it, which separates the army from
  the doctrine playing it.

## Open Questions

None that change the specs, the approach or the tasks. What the games show
about Q2 and the flag is the output of this change, not an input to it.

## Context

Four facts about the current code decide most of this design.

**The API is already render-agnostic, and deliberately so.** `http/views.py`
opens by saying it: "What a `show` command has to say, before anyone has
decided how to say it... the two formats are two renderings of one value, so
they cannot come to disagree about what is on the board the way three
hand-written `show` ladders did." `board_view` returns dimensions, rows and a
legend. A browser is a third rendering of the same value, and it needs no new
endpoint to draw a board.

**Uncommitted work is already server-side and turn-stamped.**
`Game.recordDraft` writes every accepted command to the repository, and
`_replay_draft` restores it on load — and only a draft stamped with the turn it
was drafted for. So a player can close the tab mid-turn and their orders
survive, and the interface needs no local storage to make that true. This is
the single largest thing the web tier gets for free.

**The waits already exist as long-poll.** `wait/turn` and `wait/commit` block
up to `WAIT_BUDGET` and re-check every `POLL_INTERVAL`, and `wait/commit`
returns who is still to commit. The interface's waiting screen is those two
endpoints and nothing more.

**The board is tiny and fixed.** `board-model` caps each dimension at 10, so
the largest board is a hundred squares. Every argument for a front-end
framework that rests on efficiently diffing a large tree is void here: a full
redraw of a hundred squares is imperceptible.

## Goals / Non-Goals

**Goals:**

- Somebody who has never seen a terminal can play a whole game.
- The interface is a client of the JSON API and of nothing else, so that
  anything it cannot do is a gap in the API.
- The costs a player decides by — a type's price, a move's fare, what resting
  recovers — are visible before the decision rather than after it.
- The rules that surprise people (simultaneous commit, final commit,
  visibility wiped each turn) are shown as the rules they are rather than
  discovered as defects.
- Playable from the keyboard.
- No new toolchain: the repository stays one language, and CI is unchanged.

**Non-Goals:**

- An animated, event-by-event replay of a resolution. See the decision below.
- Push transport (SSE, WebSocket). Long-poll exists and is adequate at this
  scale; the seam for push is already cut in `storage/notify.py`.
- Any change to the rules, the engine, the service layer's use cases, or the
  command-line roles.
- Programming a unit to play itself, which is what the concept is named for
  and what nothing has begun.

**Invariant untouched:** the interface neither resolves a turn nor influences
one. It posts the same commands a CLI posts, through the same endpoint, and
`board.commit()` never learns a browser was involved.

## Decisions

### The interface is a client of the JSON API, with no private back channel

No server-rendered HTML, no Jinja templates, no endpoint that exists only for
the browser except the registry, which the CLI could use too.

This is the cheapest possible test that the API is complete, and it is the
same test `ARCHITECTURE_OPTIONS.md` §6 proposed for porting the CLIs: "if a
CLI command cannot be expressed against the API, the API is wrong". If the
page needs something the API will not give it, that is a finding about the API
rather than a reason to add a template.

### No build step: vanilla ES modules and an SVG board

Rejected: a framework (React, Svelte, Vite). It would bring npm, a lockfile, a
second CI job and a second codebase into a repository that has exactly one
language and one toolchain, and the two things it would buy do not apply. Its
diffing is for trees far larger than a hundred squares. Its animation is a CSS
transition on an SVG `transform`, which is native.

Rejected: server-rendered HTML with htmx. It is a fine fit for the repository's
grain and it was the closer call. It loses on the point above — every
interaction becoming a server round trip that returns markup means the browser
and the CLI are no longer clients of one contract, and the API stops being
tested by the interface.

What replaces the framework is discipline, stated here because nothing else
will enforce it: **one state object, one render function, and no code outside
`render` touching the DOM.** A hundred squares redrawn on every change is
cheaper than the bugs that partial updates buy.

### The board is one SVG; a unit is a `<g>` that moves

Squares are drawn once from `board_view`'s dimensions. Each unit is a `<g>`
positioned by `transform: translate(...)`, keyed by name and owner. Moving a
unit between turns is a change of transform, and the CSS transition on it is
the whole animation — no timeline, no library, no frame loop.

Fog of war is a layer rather than a filter: the interface draws what the view
gives it, and the view already holds only what this seat may see
(`visibility` — "a session is given only what it may see"). The interface must
therefore never try to be clever about what to hide, because everything it has
been given is already showable.

### The seat is in the path, and the interface follows the path

`/play/<gameno>/<number>` in the page's routing, matching the API's
`/games/<gameno>/players/<number>/…`. No "current seat" in memory.

This follows from `accounts-and-membership` allowing one account several seats
in one game: a seat held in a variable would make two tabs fight, and two tabs
is exactly how somebody plays both sides. It also means a seat can be
bookmarked, which is how a person returns to a game.

### The registry is derived, not tracked

`GET /games` opens each game under the games tree and reports what it finds.
No `games` table, no row written when a game is created.

This is the pattern the codebase already uses for every fact that could
disagree with the board: elimination is "derived from the board every turn
rather than tracked, so that who is out cannot drift out of step with what is
standing", and a player's spend is derived for the same stated reason. A
tracked registry would be a fourth thing to keep in step, and its failure mode
is a lobby that lists a game that is not there or hides one that is.

The cost is that listing *n* games opens *n* games. At the scale this runs at —
tens, on one box — that is cheaper than the class of bug it avoids. If it ever
stops being true, a cache with the directory as its source of truth is the
answer, not a table.

### The resolution is shown as a change, not as a replay

`turn_events` is written on every resolution and its own schema comment says it
is "read by nothing yet". Three things stop it being the replay this interface
would like to show:

1. **It is unfiltered.** The events name every unit that acted, on both sides.
   Serving them to a player would disclose the whole board and undo
   `visibility` completely — the same defect `accounts-and-membership` exists
   to close, arriving through a different door.
2. **It is SQLite-only.** The YAML backend writes no events, so the interface
   would be richer or poorer depending on a storage flag.
3. **Filtering it is not obvious.** Roughly, a player may see an event that
   names a unit they own or a unit they had contact with that turn — but that
   needs stating as a rule, holding to `visibility`, and testing, which is a
   change rather than a task.

So: this change shows the board changing from the previous view to the new one,
and the orders the turn would not carry out, which `/state` already returns as
`rejected` and `dropped`. That is what a player needs to decide the next turn.
The replay is named as the follow-up it is, and the filtering rule is the first
thing it has to settle.

### Long-poll now, push later, and say what that costs

The interface waits on `wait/turn` and `wait/commit`. Each waiting player holds
a server thread for up to `WAIT_BUDGET` seconds, and `bgcapiserver` runs
Flask's development server — whose own docstring already says a real
deployment uses gunicorn or uwsgi. Four players in one game is four held
threads, which is fine on a laptop and not fine on a public host.

The README gains the deployment note rather than this change gaining a
transport. `storage/notify.py` already names SSE as the upgrade and says the
seam is there for it: "a future notifier that does have push semantics (SSE,
WebSocket, Redis pub/sub) can override the waiter without touching the
callers."

### The rules that surprise people are shown, not discovered

Three, each with a place in the interface:

- **A move's fare.** `ceil(max_health / 4)`, invisible today until the energy
  is gone. It goes beside every order and against the unit's reserve.
- **Resting.** A unit given no order recovers a point. Shown as `+1 rest`, not
  as an empty row, because under the rules it is a choice.
- **Lost contact.** `visibility` wipes sightings each resolution, so an enemy
  fought last turn vanishes. The interface marks it as contact lost rather
  than letting it blink out.

The third is the one worth being careful about: showing a *remembered* position
would give a player a memory the rules deny them. So it marks the loss and
shows nothing where the unit was, rather than leaving a ghost on the square.

### Keyboard play is a requirement, not an enhancement

Select a unit with the arrow keys or Tab, order it with the arrow keys, commit
with a key. A board is a grid, and a grid that can only be clicked excludes
everyone who does not use a mouse. It is also, for a game this close to chess,
simply faster.

## Risks / Trade-offs

**No framework means no guardrails.** The one-store-one-render rule is the
whole of the discipline, and nothing enforces it. If the page grows past what
that rule can carry, the honest response is to adopt a framework then, with the
API contract already proven — which is exactly the swap `ARCHITECTURE_OPTIONS.md`
§6 said staying on one contract would keep available.

**No type checking on the JavaScript, and pylint does not read it.** The
mitigation is that `tests/test_web_flow.py` drives the same JSON calls the page
makes, so the contract is tested even though the page is not. The page's own
logic is deliberately thin for this reason.

**The lobby opens every game.** Named above; acceptable at this scale, with the
answer stated if it stops being.

**Long-poll holds threads.** Named above; a deployment note rather than a
transport change.

**A first-run person has a lot to learn before a first turn.** They must
register, claim a seat, design a type, deploy units within a budget, and only
then give an order. That is the game, not the interface, but the armoury is
where it is either explained or endured — which is why the cost of a type
moves as it is designed rather than being checked afterwards.

## Migration Plan

1. Nothing to migrate. The interface is additive: no existing endpoint
   changes, no stored data changes, and no role changes.
2. Games created before this change appear in the lobby like any other, because
   the listing is derived from the games tree.
3. A deployment that does not want the interface can serve the API without the
   static directory; the endpoints are unchanged either way.

## Open Questions

1. **When may a game start?** Every seat claimed, or the administrator's call
   with unclaimed seats left empty? An empty seat is well defined — under
   `game-outcome` a player who deployed nothing is out on the first turn — but
   "well defined" and "what anybody wants" are different things. Assumed here:
   the administrator commits setup, and the lobby shows how many seats are
   still open.
2. **Should the armoury offer default unit types?** `design.md` asks for it —
   "a player wants default pieces they can select" — and a blank armoury with
   a budget is a hard first screen. Not in this change, and possibly the
   cheapest thing that would make a first game go well.
3. **How much should the interface say about a game it is not in?** The lobby
   lists games and seats. Whether it should show a game's turn number and
   board size to somebody holding no seat is a small disclosure question with
   no obvious answer.

"""Re-export of `board_game_concept.http.views`.

Kept so `show.py`, `complete.py` and every test that names
`from board_game_concept.cli import views` (or the same via `.`) does not
change. The view builders themselves live under `http/` now, because they
are also what the HTTP tier computes.
"""

from ..http.views import (
    board_view,
    direction_word,
    occupant,
    order_word,
    pending_view,
    players_view,
    state_word,
    types_view,
    units_view,
)


__all__ = [
    'board_view',
    'direction_word',
    'occupant',
    'order_word',
    'pending_view',
    'players_view',
    'state_word',
    'types_view',
    'units_view',
]

#!/usr/bin/env bash
# Play the sixth series: games 201-220 on the default board, in the draw the
# `default-board-series` change fixed before the first game was played.
#
# Each game is one `arena.py` invocation and writes its own log, so the series
# can be resumed: a game whose log already ends in an outcome line is skipped.
# Run from anywhere; the games are played out of the repository root.
#
#   matches/series.sh            # every game not yet played
#   matches/series.sh 205 206    # just these
#   PARALLEL=4 matches/series.sh # this many games at once

set -u
cd "$(dirname "$0")/.."
PYTHON="${PYTHON:-$(command -v python3)}"
if [ -x venv/bin/python ]; then PYTHON=venv/bin/python; fi
BOTS=matches/bots
PARALLEL="${PARALLEL:-1}"

# game number, player 1, player 2
DRAW="
201 garrison   garrison
202 advance    garrison
203 flag_hunt  garrison
204 screen     garrison
205 flag_hunt  lancers
206 flag_hunt  heavies
207 flag_hunt  runners
208 flag_hunt  bulwark
209 flag_hunt  executioner
210 flag_hunt  fugitive
211 lancers    heavies
212 lancers    runners
213 lancers    bulwark
214 heavies    runners
215 heavies    bulwark
216 runners    bulwark
217 executioner lancers
218 fugitive   executioner
219 flag_hunt  flag_hunt
220 advance    advance
"

played() {
    local log="matches/logs/game_$1.log"
    [ -f "$log" ] && grep -Eq '^  (game over|undecided after|not played)' "$log"
}

play() {
    local game=$1 p1=$2 p2=$3
    if played "$game"; then
        echo "game $game already played, skipping"
        return
    fi
    "$PYTHON" matches/arena.py --game "$game" \
        --p1 "$BOTS/$p1.py" --p2 "$BOTS/$p2.py" > "matches/logs/series_$game.out" 2>&1
    echo "game $game: $(grep -E '^  (game over|undecided after|not played)' "matches/logs/game_$game.log" || echo 'did not finish')"
}

mkdir -p matches/logs
wanted=("$@")
running=0
while read -r game p1 p2; do
    [ -z "$game" ] && continue
    if [ ${#wanted[@]} -gt 0 ]; then
        case " ${wanted[*]} " in *" $game "*) ;; *) continue ;; esac
    fi
    play "$game" "$p1" "$p2" &
    running=$((running + 1))
    if [ "$running" -ge "$PARALLEL" ]; then
        wait -n 2>/dev/null || wait
        running=$((running - 1))
    fi
done <<< "$DRAW"
wait

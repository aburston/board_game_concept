#!/usr/bin/env bash
# Play the seventh series: games 221-240 on the default board under the
# programmed rules, in the draw the `programmable-units` change fixed before
# the first game was played; and games 241-245, the five pairings with a
# stock seat played again under the array the `default-army-that-plays`
# change gave the game.
#
# Each game is one `arena.py` invocation and writes its own log, so the series
# can be resumed: a game whose log already ends in an outcome line is skipped.
# Run from anywhere; the games are played out of the repository root.
#
#   matches/series.sh            # every game not yet played
#   matches/series.sh 225 226    # just these
#   PARALLEL=4 matches/series.sh # this many games at once

set -u
cd "$(dirname "$0")/.."
PYTHON="${PYTHON:-$(command -v python3)}"
if [ -x venv/bin/python ]; then PYTHON=venv/bin/python; fi
BOTS=matches/bots
PARALLEL="${PARALLEL:-1}"

# game number, player 1, player 2
DRAW="
221 garrison   garrison
222 advance    garrison
223 flag_hunt  garrison
224 screen     garrison
225 flag_hunt  lancers
226 flag_hunt  heavies
227 flag_hunt  runners
228 flag_hunt  bulwark
229 flag_hunt  executioner
230 flag_hunt  fugitive
231 lancers    heavies
232 lancers    runners
233 lancers    bulwark
234 heavies    runners
235 heavies    bulwark
236 runners    bulwark
237 executioner lancers
238 fugitive   executioner
239 flag_hunt  flag_hunt
240 advance    advance
241 garrison   garrison
242 advance    garrison
243 flag_hunt  garrison
244 screen     garrison
245 flag_hunt  flag_hunt
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
        --p1 "$BOTS/$p1.yaml" --p2 "$BOTS/$p2.yaml" > "matches/logs/series_$game.out" 2>&1
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

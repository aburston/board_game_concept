# Bash completion for the board_game_concept roles.
#
# Source this file, or drop it where your shell reads completions from:
#
#     source /path/to/completions/bgc.bash
#
# A role resolves a game against the directory it is run in, as
# `games/_<gameno>`, so that is where the game numbers offered here come from
# and why the completion is worth having per directory rather than per install.
# Nothing is run to answer a completion: these are two globs over the
# directories the game is already kept in.

_bgc_game_numbers() {
    local directory
    for directory in games/_*/; do
        # an unmatched glob comes through as the pattern itself
        [ -d "$directory" ] || continue
        directory=${directory%/}
        printf '%s\n' "${directory#games/_}"
    done
}

_bgc_player_numbers() {
    local gameno=$1 file stem
    [ -n "$gameno" ] || return 0
    for file in "games/_${gameno}/players"/*.yaml; do
        [ -f "$file" ] || continue
        stem=${file##*/}
        stem=${stem%.yaml}
        # a player is `<number>.yaml`; their orders, their view and their
        # rejections are all `<number>_something.yaml` and are not players
        case $stem in
            ''|*[!0-9]*) continue ;;
        esac
        printf '%s\n' "$stem"
    done
}

_bgcclient() {
    local current=${COMP_WORDS[COMP_CWORD]}
    COMPREPLY=()
    case $COMP_CWORD in
        1) COMPREPLY=($(compgen -W "$(_bgc_game_numbers)" -- "$current")) ;;
        2) COMPREPLY=($(compgen -W "$(_bgc_player_numbers "${COMP_WORDS[1]}")" \
                        -- "$current")) ;;
    esac
}

_bgcobserver() {
    local current=${COMP_WORDS[COMP_CWORD]}
    COMPREPLY=()
    if [ "$COMP_CWORD" = 1 ]; then
        COMPREPLY=($(compgen -W "$(_bgc_game_numbers)" -- "$current"))
    fi
}

_bgcserver() {
    local current=${COMP_WORDS[COMP_CWORD]}
    local previous=${COMP_WORDS[COMP_CWORD-1]}
    COMPREPLY=()
    case $previous in
        -g|--game-number)
            COMPREPLY=($(compgen -W "$(_bgc_game_numbers)" -- "$current"))
            return
            ;;
    esac
    COMPREPLY=($(compgen -W "-g --game-number -h --help" -- "$current"))
}

complete -F _bgcclient bgcclient
complete -F _bgcobserver bgcobserver
complete -F _bgcserver bgcserver

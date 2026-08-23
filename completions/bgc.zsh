# Zsh completion for the board_game_concept roles.
#
# Source this file after compinit:
#
#     autoload -Uz compinit && compinit
#     source /path/to/completions/bgc.zsh
#
# The game numbers come from `games/_<gameno>` beneath the current directory,
# which is where a role resolves a game from, and the player numbers from the
# player files that game keeps. Nothing is run to answer a completion.

_bgc_game_numbers() {
    local directory
    local -a numbers
    for directory in games/_*(N/); do
        numbers+=( ${${directory%/}#games/_} )
    done
    compadd -a numbers
}

_bgc_player_numbers() {
    local gameno=$1 file stem
    local -a numbers
    [[ -n $gameno ]] || return 0
    for file in games/_${gameno}/players/*.yaml(N); do
        stem=${file:t:r}
        # a player is `<number>.yaml`; their orders, their view and their
        # rejections are all `<number>_something.yaml` and are not players
        [[ $stem == <-> ]] && numbers+=( $stem )
    done
    compadd -a numbers
}

_bgcclient() {
    case $CURRENT in
        2) _bgc_game_numbers ;;
        3) _bgc_player_numbers ${words[2]} ;;
    esac
}

_bgcobserver() {
    [[ $CURRENT -eq 2 ]] && _bgc_game_numbers
}

_bgcserver() {
    if [[ ${words[CURRENT-1]} == (-g|--game-number) ]]; then
        _bgc_game_numbers
        return
    fi
    compadd -- -g --game-number -h --help
}

compdef _bgcclient bgcclient
compdef _bgcserver bgcserver
compdef _bgcobserver bgcobserver

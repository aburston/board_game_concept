#!/usr/bin/env python3

import sys
from pathlib import Path

if __package__ is None:
    # launched as a script rather than imported, so put `src` on the path
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from board_game_concept.cli import complete, roles
from board_game_concept.cli.accounts import handle_account_command
from board_game_concept.cli.show import Replay, perform_show
from board_game_concept.cli.help import print_help
from board_game_concept.cli.render import print_dropped
from board_game_concept.cli.session import (describe_outcome,
                                            describe_waiting, load_game,
                                            make_accounts, make_session,
                                            read_command, read_program_file,
                                            report)
from board_game_concept.service import identity
from board_game_concept.service.commands import SetProgram
from board_game_concept.service.errors import GameError

# what a player may do to their setup, and may not once it is committed or
# the game is over
SETUP_COMMANDS = ('commit', 'add_type', 'add_unit', 'remove_unit', 'set_flag',
                  'set_program_file')
GAME_OVER = ("the game is over: your setup is committed and every turn has "
             "been played")

ROLE = roles.CLIENT

# what this role calls itself, wherever it was launched from. The prompt and
# the usage both come from here rather than from `argv[0]`, which is the path
# the process happened to be started by
PROGRAM = 'bgcclient'

DEBUG = False


def usage():
    print(f"{PROGRAM} <gameno> <player_number>", file=sys.stderr)


def main(argv=None):
    # the console script entry point calls this with nothing, so fall back to
    # the process arguments
    if argv is None:
        argv = sys.argv

    if DEBUG:
        print(f"len(argv): {len(argv)}")

    # `--server URL` picks the HTTP session; without it, `BOARD_GAME_SERVER`
    # or a local `LocalSession` decides. Kept as a `--flag URL` pair rather
    # than a positional argument so the two-argument form stays what a
    # person types today
    server = None
    token = None
    filtered = []
    it = iter(argv)
    for arg in it:
        if arg == '--server':
            try:
                server = next(it)
            except StopIteration:
                usage()
                sys.exit(1)
        elif arg.startswith('--server='):
            server = arg[len('--server='):]
        elif arg == '--token':
            try:
                token = next(it)
            except StopIteration:
                usage()
                sys.exit(1)
        elif arg.startswith('--token='):
            token = arg[len('--token='):]
        else:
            filtered.append(arg)
    argv = filtered

    if len(argv) == 3:
        gameno = argv[1]
        try:
            player_number = int(argv[2])
        except ValueError:
            usage()
            sys.exit(1)
        # checked before the game is opened, so that a caller who cannot be
        # this player is told so rather than opened as one and then refused
        # by every command they try
        if not identity.is_player(player_number):
            print(identity.out_of_range(player_number), file=sys.stderr)
            usage()
            sys.exit(1)
    else:
        usage()
        sys.exit(1)

    # a session hides how the game is reached: local when the client opens
    # a game directory itself, HTTP when it reaches the server for it
    try:
        data = make_session(gameno, player_number, server=server, token=token)
    except GameError as error:
        for line in error.lines():
            print(line, file=sys.stderr)
        sys.exit(1)

    # who this session is, asked of whatever it reached the game through:
    # the server it is talking to, or the account store beside the games
    accounts = make_accounts(data)

    # let a person at a terminal complete what they are typing. The names come
    # from this game object, which is the same one the loop below reloads into,
    # so a unit deployed during the session completes without a reload
    complete.install(ROLE, complete.GameNames(data, player_number))

    # load the data
    while True:

        # load/reload the gamedata. Patiently: a game is resolved to its
        # end under one hold the moment the last setup is committed, and a
        # client woken by that finds the game held until it is over
        load_game(data, patient=True)
        replay = Replay(data)

        outcome = data.getOutcome()
        # this player's setup is published and the game is not yet resolved:
        # the last setup is still to come, and the game is played to its end
        # the moment it does. Nothing is asked of this player until then
        if outcome is None and data.getUnprocessedMoves():
            print(f"setup committed; {describe_waiting(data.waitingOn())}")
            # blocks until the resolution has taken the setup, rather than
            # sleeping and looking again
            data.waitForTurn()
            # restart the loop, which reads the game as the resolution left it
            continue

        # a resolved game, or one this player has been wiped out of, takes no
        # more setup. Everything that reads still works, and the record is
        # there to be read: a resolved game opens at its final turn
        out_of_it = outcome is not None or data.isEliminated(player_number)
        if outcome is not None:
            print(describe_outcome(outcome))
            replay.final()
        elif out_of_it:
            print(f"player {player_number} is out of the game")

        # anything of this player's own that could not be put back when their
        # draft was restored, said before they are asked for anything else
        print_dropped(data.getDropped())

        # interactive mode
        while True:

            command = read_command(PROGRAM, ROLE)
            if command is None:
                continue

            # signing in, signing out, who am I, and changing a password are
            # the same four in every role, handled in one place
            if handle_account_command(command, accounts):
                continue

            if command.kind == 'help':
                print_help(ROLE)
                continue

            if command.kind == 'exit':
                sys.exit(0)

            if command.kind == 'show':
                perform_show(data, command, replay)
                continue

            if command.kind in ('next', 'prev'):
                replay.step(1 if command.kind == 'next' else -1)
                continue

            if out_of_it and command.kind in SETUP_COMMANDS:
                print(GAME_OVER if outcome is not None
                      else "you are out of the game")
                continue

            if command.kind == 'commit':
                # commit as this role commits - the session knows which
                # meaning by the identity it was opened as. A refusal is
                # reported and the prompt comes back, the way a refused
                # command is: a setup with nothing carrying the flag is a
                # thing to fix, not a reason to end somebody's session
                try:
                    committed = data.commit()
                except GameError as error:
                    report(error)
                    continue
                if committed:
                    print("commit complete")
                    break
                continue

            if command.kind == 'set_program_file':
                # the file is read here, on the player's side, and its text
                # is what reaches the game - a session talking to a server
                # never names a path the server owns
                try:
                    text = read_program_file(command.path)
                    data.perform(SetProgram(type_name=command.type_name,
                                            program=text))
                except GameError as error:
                    report(error)
                    continue
                perform_show(data, commands_show_program(command.type_name))
                continue

            # everything else is the service layer's to carry out or refuse,
            # and to remember: setup that is not committed yet is written
            # down as it is given, so ending the session does not lose it
            try:
                data.perform(command)
            except GameError as error:
                report(error)
                continue


def commands_show_program(type_name):
    """The `show program` that lists a program back after it is set."""
    from board_game_concept.service.commands import Show
    return Show(subject='program', name=type_name)


if __name__ == "__main__":
    main(sys.argv)

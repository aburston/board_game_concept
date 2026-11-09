"""Characterisation of the player client command surface.

One test per scenario in `openspec/specs/player-client/spec.md`. See
`test_cli_server_surface.py` for why these exist and what `expectedFailure`
means here.
"""

import unittest

from cli_harness import CliTestCase, CLIENT_PROMPT


class ClientTestCase(CliTestCase):
    """A client attached to a game that is already set up."""

    def player_client(self, players=(1,), player=1):
        self.server = self.established_game(players=players)
        client = self.start_client('test-01', player)
        client.read_until(CLIENT_PROMPT)
        return client

    def with_a_unit(self, flag=False):
        client = self.player_client()
        client.send_line('add type Cross X 1 1 10')
        client.read_until_count(CLIENT_PROMPT, 2)
        client.send_line('add unit Cross x1 0 0')
        client.read_until_count(CLIENT_PROMPT, 3)
        if flag:
            client.send_line('set flag x1')
            client.read_until_count(CLIENT_PROMPT, 4)
        return client

    def in_play(self):
        """Past setup: the player has committed and the game has been played.

        The sole player's commit satisfies the barrier, the server resolves
        the whole game - one unit with no controller stands where it was put,
        so the state repeats on turn 2 and the game stops undecided - and
        the client is shown the result and the final turn.
        """
        client = self.with_a_unit(flag=True)
        client.send_line('commit')
        client.read_until('commit complete')
        client.read_until('game over', timeout=60)
        client.read_until_count(CLIENT_PROMPT, 5, timeout=60)
        return client

    def program_file(self, text, name='program_under_test.asm'):
        """A program written where the client runs, for `set program`."""
        from cli_harness import TEST_DIR
        path = TEST_DIR / name
        path.write_text(text)
        self.addCleanup(lambda: path.unlink(missing_ok=True))
        return name


class CarryingTheFlag(ClientTestCase):
    """`set flag <unit>`, and what a setup without one is told."""

    def test_designating_a_carrier(self):
        client = self.with_a_unit()
        client.send_line('set flag x1')
        client.read_until_count(CLIENT_PROMPT, 4)
        shown = self.shown(client, CLIENT_PROMPT, 'show units')
        assert 'FLAG' in shown
        assert shown.splitlines()[1].split()[-1] == 'yes'

    def test_designating_a_unit_that_is_not_yours(self):
        client = self.with_a_unit()
        client.send_line('set flag nobody')
        client.read_until('there is no unit of yours called nobody')

    def test_wrong_argument_count(self):
        client = self.with_a_unit()
        client.send_line('set flag')
        client.read_until('must provide the name of one of your units')

    def test_committing_a_setup_with_no_carrier(self):
        client = self.with_a_unit()
        client.send_line('commit')
        client.read_until('must carry your flag')

    def test_designating_after_the_setup_is_committed(self):
        client = self.in_play()
        client.send_line('set flag x1')
        client.read_until('the game is over: your setup is committed')

    def test_showing_the_flags(self):
        client = self.in_play()
        shown = self.shown(client, CLIENT_PROMPT, 'show flags')
        assert shown.splitlines()[0].split() == ['PLAYER', 'X', 'Y',
                                                 'STANDING']
        assert shown.splitlines()[1].split() == ['1', '0', '0', 'yes']


class ClientInvocation(CliTestCase):

    def test_starting_a_client(self):
        self.established_game(players=(1,))
        client = self.start_client('test-01', 1)
        client.read_until(CLIENT_PROMPT)

    def test_wrong_arguments(self):
        client = self.start_client_with_args(['test-01'])
        self.assertNotEqual(0, client.wait_for_exit())
        self.assertIn('bgcclient <gameno> <player_number>', client.errors)

    def test_unknown_game(self):
        client = self.start_client('no-such-game', 1)
        self.assertNotEqual(0, client.wait_for_exit())
        self.assertIn('No game with path', client.errors)

    def test_console_script_entry_point(self):
        # the generated console script calls main() with no arguments at all
        client = self.start_entry_point('client')
        self.assertNotEqual(0, client.wait_for_exit())
        self.assertIn('bgcclient <gameno> <player_number>', client.errors)
        self.assertNotIn('TypeError', client.errors)


class ClientCommandLoop(ClientTestCase):

    def test_blank_input(self):
        client = self.player_client()
        client.send_line('')
        client.read_until_count(CLIENT_PROMPT, 2)
        self.assertNotIn('invalid', client.since(CLIENT_PROMPT))

    def test_unrecognised_command(self):
        client = self.player_client()
        client.send_line('wibble')
        client.read_until('invalid command')

    def test_help_lists_commands(self):
        client = self.player_client()
        client.send_line('help')
        client.read_until('commit')
        for command in ('add type', 'add unit', 'show board', 'show types',
                        'show units', 'move', 'exit'):
            self.assertIn(command, client.output)

    def test_exit_ends_the_session(self):
        client = self.player_client()
        client.send_line('exit')
        self.assertEqual(0, client.wait_for_exit())


class DefiningUnitTypes(ClientTestCase):

    def test_defining_a_type(self):
        client = self.player_client()
        client.send_line('add type Cross X 1 1 10')
        client.read_until_count(CLIENT_PROMPT, 2)
        lines = self.shown_table(client, CLIENT_PROMPT, 'types')
        # the table also lists the catalogue this player was registered with,
        # so the type just defined is looked for rather than counted to
        rows = [line.split() for line in lines[1:]]
        assert ['1', 'Cross', 'X', '1', '1', '10', '0', 'no', '12'] in rows

    def test_wrong_argument_count(self):
        client = self.player_client()
        client.send_line('add type')
        client.read_until('must provide 5 args for type')

    def test_invalid_statistics(self):
        client = self.player_client()
        client.send_line('add type Cross X 99 1 10')
        client.read_until(
            'error adding unit type: attack must be a value from 0 to 10')

    def test_taking_a_unit_back(self):
        client = self.player_client()
        client.send_line('add type Cross X 1 1 10')
        client.read_until_count(CLIENT_PROMPT, 2)
        client.send_line('add unit Cross x1 0 0')
        client.read_until_count(CLIENT_PROMPT, 3)

        client.send_line('remove unit x1')
        client.read_until_count(CLIENT_PROMPT, 4)

        units = self.shown_json(client, CLIENT_PROMPT, 'units')['units']
        assert [unit['name'] for unit in units] == []

    def test_taking_back_a_unit_that_is_not_there(self):
        client = self.player_client()
        client.send_line('remove unit nobody')
        client.read_until('no unit of yours is called nobody')

    def test_a_type_with_no_energy_can_have_no_attack(self):
        client = self.player_client()
        client.send_line('add type Half H 3 10 0')
        client.read_until('error adding unit type: a type with no energy can '
                          'have no attack')

    def test_a_type_with_no_attack_may_have_energy(self):
        # a scout: it goes where it likes and strikes nothing
        client = self.player_client()
        client.send_line('add type Scout S 0 4 6')
        client.read_until_count(CLIENT_PROMPT, 2)
        self.assertNotIn('error adding unit type', client.output)

    def test_a_type_that_cannot_afford_a_move_is_refused(self):
        client = self.player_client()
        # health 6 costs 2 to move, so 1 energy is a design that could never
        # take a step
        # ...for a type that thinks. One with no compute is a turret, and
        # exempt
        client.send_line('add type Heavy H 3 6 1 1')
        client.read_until('error adding unit type: a type that can move must '
                          'have at least its movement cost in energy')

    def test_defining_a_wall(self):
        client = self.player_client()
        client.send_line('add type Wall W 0 10 0')
        client.send_line('show types')
        client.read_until('Wall')

    def test_defining_a_type_after_setup(self):
        client = self.in_play()
        client.send_line('add type Later L 1 1 10')
        client.read_until('the game is over: your setup is committed')

    def test_defining_a_type_with_compute(self):
        client = self.player_client()
        client.send_line('add type Runner r 2 4 10 5')
        client.read_until_count(CLIENT_PROMPT, 2)
        lines = self.shown_table(client, CLIENT_PROMPT, 'types')
        assert 'COMPUTE' in lines[0].split()
        runner = [line.split() for line in lines[1:]
                  if line.split()[1] == 'Runner'][0]
        assert runner[lines[0].split().index('COMPUTE')] == '5'
        # compute is bought like the other three: 2 + 4 + 10 + 5
        assert runner[lines[0].split().index('COST')] == '21'


class DeployingUnits(ClientTestCase):

    def test_deploying_a_unit(self):
        client = self.with_a_unit()
        client.send_line('show board')
        client.read_until('X')

    def test_a_deployed_unit_is_drawn(self):
        client = self.with_a_unit()
        client.send_line('show board')
        client.read_until('X')

    def test_wrong_argument_count(self):
        client = self.player_client()
        client.send_line('add unit')
        client.read_until('must provide 4 args for unit')

    def test_unknown_type(self):
        client = self.player_client()
        client.send_line('add type Cross X 1 1 10')
        client.read_until_count(CLIENT_PROMPT, 2)
        client.send_line('add unit Nope n1 0 0')
        client.read_until('error creating new unit')

    def test_coordinates_outside_the_board(self):
        client = self.player_client()
        client.send_line('add type Cross X 1 1 10')
        client.read_until_count(CLIENT_PROMPT, 2)
        client.send_line('add unit Cross x1 9 9')
        client.read_until('are out of bounds for this board')

    def test_deploying_onto_a_cell_the_player_already_holds(self):
        client = self.with_a_unit()
        client.send_line('add unit Cross x2 0 0')
        client.read_until("that square is occupied")
        # the session survives the refusal
        client.send_line('add unit Cross x2 1 1')
        client.read_until_count(CLIENT_PROMPT, 5)

    def test_reusing_a_unit_name(self):
        client = self.with_a_unit()
        client.send_line('add unit Cross x1 2 2')
        client.read_until('error creating new unit')

    def test_deploying_after_setup(self):
        client = self.in_play()
        client.send_line('add unit Cross x9 2 2')
        client.read_until('the game is over: your setup is committed')

    def test_deploying_more_than_the_budget_can_pay_for(self):
        client = self.player_client(players=((1, 30),))
        client.send_line('add type Cross X 1 10 10')
        client.read_until_count(CLIENT_PROMPT, 2)
        client.send_line('add unit Cross x1 0 0')
        client.read_until_count(CLIENT_PROMPT, 3)
        # 21 spent of 30, so a second costs more than the 9 that are left
        client.send_line('add unit Cross x2 1 1')
        client.read_until('costs 21 points')
        client.read_until('9 of player 1')
        client.read_until('30-point budget')
        # the session survives the refusal, and the square is still free
        client.send_line('show units')
        client.read_until_count(CLIENT_PROMPT, 5)


class SettingAProgram(ClientTestCase):
    """`set program <type> <file>` and `show program <type>`."""

    HUNT = 'SELF\nFLAG enemy\nJIF neg r0, rest\nMOVE south\nHALT\nrest: SLEEP 2\n'

    def a_thinking_type(self):
        client = self.player_client()
        client.send_line('add type Runner r 2 4 10 3')
        client.read_until_count(CLIENT_PROMPT, 2)
        return client

    def test_setting_a_program(self):
        client = self.a_thinking_type()
        path = self.program_file(self.HUNT)
        lines = self.shown(client, CLIENT_PROMPT,
                           f'set program Runner {path}').splitlines()
        # the program is listed back with the tick cost of each line
        assert lines[0] == ('Runner: compute 3, 300 ticks per energy, '
                            'cap 300 ticks a turn')
        assert lines[1].split() == ['LINE', 'TICKS', 'PROGRAM']
        assert lines[2].split()[:3] == ['1', '1', 'SELF']
        assert lines[-1] == 'a straight run costs 6 ticks'

    def test_a_program_with_a_bad_line(self):
        client = self.a_thinking_type()
        good = self.program_file(self.HUNT)
        client.send_line(f'set program Runner {good}')
        client.read_until_count(CLIENT_PROMPT, 3)
        bad = self.program_file('SELF\nFLY away\n', name='bad.asm')
        client.send_line(f'set program Runner {bad}')
        client.read_until('line 2')
        # the type's program is as it was
        shown = self.shown(client, CLIENT_PROMPT, 'show program Runner')
        assert 'FLAG enemy' in shown and 'FLY' not in shown

    def test_a_program_on_a_type_with_no_controller(self):
        client = self.with_a_unit()          # Cross has compute 0
        path = self.program_file(self.HUNT)
        client.send_line(f'set program Cross {path}')
        client.read_until('has compute 0, so it has no controller')

    def test_a_program_after_commit(self):
        client = self.in_play()
        path = self.program_file(self.HUNT)
        client.send_line(f'set program Cross {path}')
        client.read_until('the game is over: your setup is committed')

    def test_a_file_that_cannot_be_read(self):
        client = self.a_thinking_type()
        client.send_line('set program Runner nowhere.asm')
        client.read_until('cannot read the program file nowhere.asm')

    def test_reading_a_program_back(self):
        client = self.a_thinking_type()
        path = self.program_file(self.HUNT)
        client.send_line(f'set program Runner {path}')
        client.read_until_count(CLIENT_PROMPT, 3)
        lines = self.shown(client, CLIENT_PROMPT,
                           'show program Runner').splitlines()
        assert lines[0] == ('Runner: compute 3, 300 ticks per energy, '
                            'cap 300 ticks a turn')
        # a jump costs a tick, a HALT nothing, and the label line is its
        # instruction's
        by_line = {line.split()[0]: line.split()[1] for line in lines[2:-1]}
        assert by_line['3'] == '1' and by_line['5'] == '0'
        assert lines[-1] == 'a straight run costs 6 ticks'

    def test_a_type_without_a_program(self):
        client = self.a_thinking_type()
        shown = self.shown(client, CLIENT_PROMPT, 'show program Runner')
        assert 'no program' in shown

    def test_wrong_argument_count(self):
        client = self.player_client()
        client.send_line('set program Runner')
        client.read_until('must provide a type and the file holding its '
                          'program')

    def test_there_is_no_move_command(self):
        client = self.in_play()
        client.send_line('move x1 north')
        client.read_until('invalid command')


class ClientDisplayCommands(ClientTestCase):

    def test_showing_the_board(self):
        client = self.player_client()
        client.send_line('show board')
        client.read_until('+-')

    def test_showing_types(self):
        client = self.player_client()
        client.send_line('add type Cross X 1 1 10')
        client.read_until_count(CLIENT_PROMPT, 2)
        lines = self.shown_table(client, CLIENT_PROMPT, 'types')
        assert lines[0].split() == [
            'PLAYER', 'NAME', 'SYMBOL', 'ATTACK', 'HEALTH', 'ENERGY',
            'COMPUTE', 'PROGRAM', 'COST']
        rows = [line.split() for line in lines[1:]]
        assert ['1', 'Cross', 'X', '1', '1', '10', '0', 'no', '12'] in rows
        assert ['1', 'Heavy', 'H', '5', '10', '15', '4', 'yes', '34'] in rows, (
            'the catalogue is listed alongside it, compute and program too')

    def test_showing_units(self):
        client = self.with_a_unit()
        lines = self.shown_table(client, CLIENT_PROMPT, 'units')
        assert lines[0].split() == [
            'PLAYER', 'NAME', 'TYPE', 'SYMBOL', 'ATTACK', 'HEALTH', 'ENERGY',
            'X', 'Y', 'STATE', 'DIRECTION', 'FLAG']
        # the last `-` is `FLAG`: this unit carries nothing
        assert lines[1].split() == [
            '1', 'x1', 'Cross', 'X', '1', '1', '10', '0', '0', 'holding',
            '-', '-']

    def test_showing_units_before_any_are_deployed(self):
        client = self.player_client()
        assert self.shown(client, CLIENT_PROMPT, 'show units') == 'no units yet'

    def test_showing_players(self):
        client = self.player_client()
        lines = self.shown_table(client, CLIENT_PROMPT, 'players')
        assert lines[0].split() == [
            'PLAYER', 'STATUS', 'BUDGET', 'SPENT', 'LEFT']
        # a player reads their own points, and a `-` where another player's
        # record was never theirs to read
        assert ['1', 'active', '320', '0', '320'] in [
            line.split() for line in lines[1:]]

    def test_another_players_points_are_not_shown(self):
        client = self.player_client(players=(1, 2), player=1)
        lines = self.shown_table(client, CLIENT_PROMPT, 'players')
        rows = {line.split()[0]: line.split() for line in lines[1:]}
        # player 2's record is not this session's to read, so the three point
        # columns have nothing to put in them
        assert rows['2'][2:] == ['-', '-', '-']

    def test_showing_the_board_with_a_legend(self):
        client = self.with_a_unit()
        lines = self.shown_table(client, CLIENT_PROMPT, 'board')
        assert lines[0].startswith('+-+')
        legend = lines[lines.index('SYMBOL  PLAYER  TYPE'):]
        assert legend[1].split() == ['X', '1', 'Cross']

    def test_showing_a_subject_as_json(self):
        client = self.with_a_unit()
        document = self.shown_json(client, CLIENT_PROMPT, 'units')
        assert document['units'] == [{
            'player': 1, 'name': 'x1', 'type': 'Cross', 'symbol': 'X',
            'attack': 1, 'health': 1, 'energy': 10, 'x': 0, 'y': 0,
            'state': 'holding', 'direction': None, 'flag': False}]

    def test_the_json_holds_no_storage_field(self):
        client = self.with_a_unit()
        document = self.shown_json(client, CLIENT_PROMPT, 'units')
        for storage_only in ('type_attack', 'type_health', 'type_energy',
                             'on_board', 'destroyed', 'id'):
            assert storage_only not in document['units'][0]

    def test_the_table_and_the_json_describe_the_same_units(self):
        client = self.with_a_unit()
        rows = self.shown_table(client, CLIENT_PROMPT, 'units')[1:]
        document = self.shown_json(client, CLIENT_PROMPT, 'units')

        assert len(rows) == len(document['units'])
        for row, entry in zip(rows, document['units']):
            cells = row.split()
            assert cells[1] == entry['name']
            assert cells[0] == str(entry['player'])
            assert cells[5] == str(entry['health'])
            assert cells[9] == entry['state']

    def test_the_board_as_json(self):
        client = self.with_a_unit()
        document = self.shown_json(client, CLIENT_PROMPT, 'board')
        board = document['board']
        assert (board['size_x'], board['size_y']) == (4, 4)
        assert board['rows'][0][0] == 'X'
        assert board['legend'] == [
            {'symbol': 'X', 'player': 1, 'type': 'Cross'}]

    def test_a_trailing_word_that_is_not_json(self):
        client = self.player_client()
        assert self.shown(
            client, CLIENT_PROMPT,
            'show units wibble') == 'invalid show command'

    def test_incomplete_show_command(self):
        client = self.player_client()
        client.send_line('show')
        client.read_until('invalid show command')

    def test_unrecognised_show_subject(self):
        client = self.player_client()
        client.send_line('show wibble')
        client.read_until('invalid show command')


class CommittingATurn(ClientTestCase):

    def test_committing(self):
        client = self.with_a_unit(flag=True)
        client.send_line('commit')
        client.read_until('commit complete')
        # the sole player's was the last setup outstanding, so the game is
        # resolved and the client shows its result and final turn
        client.read_until('game over: undecided on turn 2', timeout=60)
        client.read_until('turn 2')
        client.read_until_count(CLIENT_PROMPT, 5, timeout=60)

    def test_committing_waits_for_the_other_setups(self):
        self.server = self.established_game(players=(1, 2))
        client = self.start_client('test-01', 1)
        client.read_until(CLIENT_PROMPT)
        client.send_line('add type Cross X 1 1 10')
        client.read_until_count(CLIENT_PROMPT, 2)
        client.send_line('add unit Cross x1 0 0')
        client.read_until_count(CLIENT_PROMPT, 3)
        client.send_line('set flag x1')
        client.read_until_count(CLIENT_PROMPT, 4)
        client.send_line('commit')
        client.read_until('commit complete')
        client.read_until('waiting for player(s) 2 to commit their setup')

    def test_reloading_after_resolution(self):
        client = self.in_play()
        # back at the prompt, with the game to read
        client.send_line('show board')
        client.read_until('X')


class WatchingTheReplay(ClientTestCase):
    """`show turn <n>`, `next`, `prev` and `show turn <n> known`."""

    def test_opening_a_resolved_game(self):
        self.in_play()
        again = self.start_client('test-01', 1)
        again.read_until('game over: undecided on turn 2')
        again.read_until('turn 2')
        again.read_until(CLIENT_PROMPT)

    def test_reading_a_turn(self):
        client = self.in_play()
        shown = self.shown(client, CLIENT_PROMPT, 'show turn 1')
        lines = shown.splitlines()
        assert lines[0] == 'turn 1'
        # the board after turn 1, with the unit on it
        assert '|X| | | |' in lines
        # what the turn did to the player's units
        assert 'x1 is placed at (0, 0)' in shown

    def test_stepping_through(self):
        client = self.in_play()
        self.shown(client, CLIENT_PROMPT, 'show turn 1')
        assert self.shown(client, CLIENT_PROMPT, 'next').splitlines()[0] \
            == 'turn 2'
        assert self.shown(client, CLIENT_PROMPT, 'prev').splitlines()[0] \
            == 'turn 1'
        # the record begins with the setup resolution, turn 0, and ends
        # where the game did
        assert self.shown(client, CLIENT_PROMPT, 'prev').splitlines()[0] \
            == 'turn 0'
        assert 'the record has no turn -1; it holds turns 0 to 2' in \
            self.shown(client, CLIENT_PROMPT, 'prev')

    def test_what_my_army_knew(self):
        client = self.in_play()
        lines = self.shown(client, CLIENT_PROMPT,
                           'show turn 1 known').splitlines()
        # the player's unit where it stands, the rest of the board unknown
        assert '|X|?|?|?|' in lines
        assert any(line.split()[:1] == ['?'] for line in lines)

    def test_a_turn_the_record_does_not_hold(self):
        client = self.in_play()
        shown = self.shown(client, CLIENT_PROMPT, 'show turn 9')
        assert 'the record has no turn 9; it holds turns 0 to 2' in shown

    def test_before_the_game_is_resolved(self):
        self.server = self.established_game(players=(1, 2))
        client = self.start_client('test-01', 1)
        client.read_until(CLIENT_PROMPT)
        client.send_line('show turn 1')
        client.read_until('the game has not been resolved: waiting for '
                          'player(s) 1, 2 to commit their setup')
        client.send_line('next')
        client.read_until_count('the game has not been resolved', 2)

    def test_the_turn_as_json(self):
        import json
        client = self.in_play()
        document = json.loads(self.shown(client, CLIENT_PROMPT,
                                         'show turn 1 json'))
        assert document['turn']['turn'] == 1
        assert document['turn']['board']['rows'][0][0] == 'X'


class ReportingRejectedOrders(ClientTestCase):

    def test_nothing_was_rejected(self):
        client = self.in_play()
        self.assertNotIn('rejected', client.output)


if __name__ == '__main__':
    unittest.main()

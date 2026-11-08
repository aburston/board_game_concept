"""The program parser: what a type's program is allowed to say.

A program is checked when it is set, not when it runs: an instruction the
set does not have, an operand of the wrong kind, a jump to nowhere or a sleep
outside its bounds is refused naming the line. What a program would *do* is
never a reason to refuse it.
"""

import pytest

from board_game_concept.domain.program import (
    MAX_SLEEP, TICKS, Program, ProgramError)


EVERY_INSTRUCTION = """
start:
    SELF
    TURN
    EXTENT
    FLAG mine
    FLAG enemy
    MAP r0, r1
    NEAREST friend
    NEAREST enemy
    NEAREST unknown
    CONTACT
    RECV
    FLUSH
    SET r0, 5
    MOV r1, r0
    ADD r0, r1
    ADD r0, 3
    SUB r0, r1
    SUB r0, -2
    ABS r0
    SIGN r0
    DIST r0, r1
    LOAD r2, 7
    LOAD r2, r0
    STORE r2, 7
    STORE r2, r0
    JMP next
next:
    JIF zero r0, next2
next2:
    JIF notzero r0, next3
next3:
    JIF neg r0, next4
next4:
    JIF pos r0, next5
next5:
    JIF eq r0, r1, next6
next6:
    JIF lt r0, r1, done
    MOVE north
    MOVE east
    MOVE south
    MOVE west
    MOVE r0
    HOLD
    SAY all, 1, r0, 3
    SAY runner1, r1, r2, r3
    SLEEP 1
    SLEEP 100
done:
    HALT
"""


def test_every_instruction_parses():
    program = Program(EVERY_INSTRUCTION)
    ops = {instruction.op for instruction in program.instructions}
    assert ops == set(TICKS)


def test_an_empty_program_parses():
    assert len(Program('')) == 0
    assert len(Program('; nothing but a comment\n\n')) == 0
    assert Program(None).ticks == 0


def test_comments_and_blank_lines_are_ignored():
    program = Program('SELF ; who am I\n\n  ; a note\nHOLD')
    assert [i.op for i in program.instructions] == ['SELF', 'HOLD']


def test_commas_are_optional():
    assert Program('SET r0 5\nADD r0 r1').ticks == 2
    assert Program('SET r0, 5\nADD r0, r1').ticks == 2


def test_the_listing_prices_each_line():
    program = Program('SELF\n\nNEAREST enemy ; look\nSAY all, 1, 2, 3')
    listing = program.listing()
    assert [(n, ticks) for n, _text, ticks in listing] == [
        (1, 1), (2, None), (3, 4), (4, 5)]
    assert program.ticks == 10


@pytest.mark.parametrize('line', [
    'JUMP start', 'THINK', 'MOVE sideways', 'FLAG theirs',
    'NEAREST wall', 'SET r0', 'SET r0, r1', 'MAP r0, 3', 'ADD 3, r0',
    'JIF maybe r0, start', 'JIF zero, start', 'SAY all, 1, 2',
    'SLEEP r0', 'SLEEP', 'LOAD 7, r0', 'MOV r0, 1', 'ABS 3', 'SELF r0',
    'SET r8, 1', 'SET R0, 1',
])
def test_a_bad_line_is_refused_naming_it(line):
    with pytest.raises(ProgramError) as refused:
        Program(f'start:\nSELF\n{line}\n')
    assert refused.value.line == 3


def test_a_jump_to_a_missing_label_is_refused():
    with pytest.raises(ProgramError) as refused:
        Program('SELF\nJMP nowhere')
    assert refused.value.line == 2
    assert 'nowhere' in str(refused.value)


def test_a_label_defined_twice_is_refused():
    with pytest.raises(ProgramError) as refused:
        Program('a:\nSELF\na:\nHOLD')
    assert refused.value.line == 3


@pytest.mark.parametrize('n', [0, -1, MAX_SLEEP + 1, 1000])
def test_a_sleep_outside_its_bounds_is_refused(n):
    with pytest.raises(ProgramError) as refused:
        Program(f'SLEEP {n}')
    assert refused.value.line == 1
    assert str(MAX_SLEEP) in str(refused.value)


def test_a_program_that_would_loop_for_ever_is_accepted():
    program = Program('loop:\nSELF\nJMP loop')
    assert len(program) == 2


def test_a_label_may_share_a_line_with_an_instruction():
    program = Program('loop: SELF\nJMP loop')
    assert program.labels == {'loop': 0}

"""The preprocessor: the macro language a program's text is written in.

A program is expanded before it is checked, priced or run. These hold the
expansion to the spec: what each directive does, what a macro costs (nothing
- its expansion costs what it costs), that nothing is read from a file, and
that every refusal, listing and halt speaks of the line the player wrote.
"""

import builtins

import pytest

from board_game_concept.domain import preprocess
from board_game_concept.domain.preprocess import (
    HEADERS, MAX_DEPTH, MAX_LINES, UNIT_H, ProgramError, expand)
from board_game_concept.domain.program import Program, Snapshot, run


def texts(program):
    return [line.text for line in expand(program)]


# --- expansion before checking

def test_a_program_with_no_directive_expands_to_itself():
    text = 'start:\nSELF ; look\n\n  MOV r6, r0\nJMP start'
    assert [(e.line, e.macro, e.text) for e in expand(text)] == [
        (1, None, 'start:'), (2, None, 'SELF'), (4, None, 'MOV r6, r0'),
        (5, None, 'JMP start')]
    assert Program(text).ticks == 3


def test_a_program_with_a_macro():
    program = Program('#define GO_HOME JMP home\nhome: SELF\nGO_HOME')
    assert [(i.op, i.args) for i in program.instructions] == [
        ('SELF', ()), ('JMP', (('word', 'home'),))]


def test_expansion_is_the_same_every_time():
    text = '#include <unit.h>\nSTEP(east)\nIF_NEG(MY_ENERGY, rest)\nrest: REST'
    assert texts(text) == texts(text)


# --- object-like macros

def test_naming_a_register():
    assert texts('#define here_x r6\nMOV here_x, r0') == ['MOV r6, r0']


def test_naming_a_number():
    assert texts('#define FRIEND 2\nSUB r0, FRIEND') == ['SUB r0, 2']


def test_part_of_a_word_is_not_a_macro():
    assert texts('#define x r0\nnext: SELF\nJMP next') == [
        'next: SELF', 'JMP next']


def test_comments_are_left_alone():
    program = Program('#define SELF HOLD\nHOLD ; SELF is not expanded here')
    assert program.listing() == [
        (1, '#define SELF HOLD', None),
        (2, 'HOLD ; SELF is not expanded here', 1)]


def test_a_conflicting_redefinition_is_refused():
    with pytest.raises(ProgramError) as refused:
        expand('#define SPEED 1\nSELF\n#define SPEED 2')
    assert refused.value.line == 3
    assert 'SPEED' in str(refused.value)


def test_the_same_definition_twice_is_allowed():
    assert texts('#define SPEED 1\n#define SPEED  1\nSET r0, SPEED') == [
        'SET r0, 1']


def test_undef_frees_a_name():
    assert texts('#define SPEED 1\n#undef SPEED\n#define SPEED 2\n'
                 'SET r0, SPEED') == ['SET r0, 2']


def test_a_macro_that_names_itself_expands_once():
    with pytest.raises(ProgramError) as refused:
        Program('#define LOOP LOOP\nLOOP')
    assert refused.value.line == 2
    assert 'LOOP is not an instruction' in str(refused.value)


# --- function-like macros

def test_an_inline_function():
    assert texts('#define IF_BELOW(a, b, where) JIF lt a, b, where\n'
                 'IF_BELOW(r0, r3, gocol)') == ['JIF lt r0, r3, gocol']


def test_arguments_are_expanded():
    assert texts('#define here_x r6\n'
                 '#define IF_BELOW(a, b, where) JIF lt a, b, where\n'
                 'IF_BELOW(here_x, r3, gocol)') == ['JIF lt r6, r3, gocol']


def test_too_few_arguments_are_refused():
    with pytest.raises(ProgramError) as refused:
        expand('#define TWO(a, b) ADD a, b\nSELF\nTWO(r0)')
    assert refused.value.line == 3
    assert 'TWO' in str(refused.value)


def test_pasting_a_label():
    assert texts('#define GO(dir) JMP go_ ## dir\nGO(east)') == [
        'JMP go_east']


def test_a_function_name_without_parentheses_is_a_word():
    assert texts('#define STEP(d) MOVE d\nSTEP') == ['STEP']


# --- several instructions, private labels

def test_a_multi_instruction_macro():
    program = Program('#define STEP_EAST MOVE east \\\n    HALT\n'
                      'SELF\nSTEP_EAST')
    assert [i.op for i in program.instructions] == ['SELF', 'MOVE', 'HALT']
    assert [i.line for i in program.instructions] == [3, 4, 4]
    assert program.listing()[3] == (4, 'STEP_EAST', 1)


def test_a_branching_macro_used_twice():
    text = ('#define SKIP_IF_ZERO(r, what) JIF zero r, @skip \\\n'
            '    what \\\n'
            '@skip:\n'
            'SKIP_IF_ZERO(r0, MOVE north)\n'
            'SKIP_IF_ZERO(r1, MOVE south)\n'
            'HALT')
    program = Program(text)
    labels = sorted(program.labels)
    assert len(labels) == 2 and all(label.startswith('_m') for label in labels)
    assert labels[0] != labels[1]


def test_a_private_label_outside_a_macro_is_refused():
    with pytest.raises(ProgramError) as refused:
        expand('SELF\n@skip: HOLD')
    assert refused.value.line == 2


def test_a_reserved_name_is_refused():
    with pytest.raises(ProgramError) as refused:
        expand('_m1_skip: HOLD')
    assert refused.value.line == 1


# --- conditionals

def test_a_default_a_program_may_override():
    text = '#ifndef TARGET\n#define TARGET FLAG enemy\n#endif\nTARGET'
    assert texts(text) == ['FLAG enemy']
    assert texts('#define TARGET NEAREST enemy\n' + text) == ['NEAREST enemy']


def test_ifdef_else_and_nesting():
    text = ('#define A\n#ifdef A\n#ifdef B\nSET r0, 1\n#else\nSET r0, 2\n'
            '#endif\n#else\nSET r0, 3\n#endif')
    assert texts(text) == ['SET r0, 2']
    assert texts('#define B\n' + text) == ['SET r0, 1']
    assert texts(text.replace('#define A\n', '')) == ['SET r0, 3']


def test_a_missing_endif_is_refused_at_the_ifdef():
    with pytest.raises(ProgramError) as refused:
        expand('SELF\n#ifdef X\nHOLD')
    assert refused.value.line == 2


def test_a_stray_else_or_endif_is_refused():
    with pytest.raises(ProgramError):
        expand('#endif')
    with pytest.raises(ProgramError):
        expand('#else')


def test_a_deliberate_error():
    with pytest.raises(ProgramError) as refused:
        expand('#ifndef NEED\n#error set NEED first\n#endif')
    assert refused.value.line == 2
    assert refused.value.message == 'set NEED first'
    assert texts('#define NEED 3\n#ifndef NEED\n#error no\n#endif\nSELF') == [
        'SELF']


def test_an_unknown_directive_is_refused():
    with pytest.raises(ProgramError) as refused:
        expand('SELF\n#pragma once')
    assert refused.value.line == 2


# --- headers

def test_including_the_unit_header():
    assert texts('#include <unit.h>\nSET r0, SOUTH\nSUB SEEN, FRIEND') == [
        'SET r0, 3', 'SUB r0, 2']


def test_a_header_is_included_once():
    assert texts('#include <unit.h>\n#include <unit.h>\nSET r0, WEST') == [
        'SET r0, 4']


def test_including_a_file_is_refused_and_reads_nothing(monkeypatch):
    def no_open(*args, **kwargs):
        raise AssertionError('the preprocessor opened a file')
    monkeypatch.setattr(builtins, 'open', no_open)
    for line in ('#include "orders.asm"', '#include </etc/passwd>',
                 '#include <nothing.h>', '#include unit.h'):
        with pytest.raises(ProgramError) as refused:
            expand('SELF\n' + line)
        assert refused.value.line == 2
    assert texts('#include <unit.h>\nREST') == ['SLEEP 1']


def test_the_headers_are_published():
    assert HEADERS == {'unit.h': UNIT_H}


# --- unit.h

def test_directions_and_map_answers():
    text = ('#include <unit.h>\nSET r0, NORTH\nSET r0, EAST\nSET r0, SOUTH\n'
            'SET r0, WEST\nSET r0, UNKNOWN\nSET r0, EMPTY\nSET r0, FRIEND\n'
            'SET r0, ENEMY\nSET r0, OFF_BOARD')
    assert texts(text) == [f'SET r0, {n}' for n in (1, 2, 3, 4, 0, 1, 2, 3, 4)]


@pytest.mark.parametrize('use, expansion', [
    ('MOV r6, MY_X', ['MOV r6, r0']),
    ('MOV r7, MY_Y', ['MOV r7, r1']),
    ('SUB MY_ENERGY, 3', ['SUB r3, 3']),
    ('MOV r6, FOUND_X', ['MOV r6, r0']),
    ('MOV r6, FOUND_DIST', ['MOV r6, r2']),
    ('SUB SEEN, 2', ['SUB r0, 2']),
    ('GOTO(there)', ['JMP there']),
    ('IF_ZERO(r0, there)', ['JIF zero r0, there']),
    ('IF_NONZERO(r0, there)', ['JIF notzero r0, there']),
    ('IF_NEG(r0, there)', ['JIF neg r0, there']),
    ('IF_POS(r0, there)', ['JIF pos r0, there']),
    ('IF_EQ(r0, r1, there)', ['JIF eq r0, r1, there']),
    ('IF_BELOW(r0, r1, there)', ['JIF lt r0, r1, there']),
    ('IF_NONE(FOUND_X, there)', ['JIF neg r0, there']),
    ('IF_FOUND(GOT_MESSAGE, there)', ['JIF pos r0, there']),
    ('STEP(east)', ['MOVE east', 'HALT']),
    ('STEP(r4)', ['MOVE r4', 'HALT']),
    ('STAY', ['HOLD', 'HALT']),
    ('REST', ['SLEEP 1']),
    ('REST_LONG', ['SLEEP 100']),
    ('UNLESS_AFFORD(3, rest)', ['SELF', 'SUB r3, 3', 'JIF neg r3, rest']),
    ('LOOK_AT(r6, r7)', ['MAP r6, r7']),
    ('IF_SEEN(FRIEND, there)', ['SET r1, 2', 'JIF eq r0, r1, there']),
    ('ROW_STEP(r4, r0)', ['SET r0, 3', 'SUB r0, r4']),
    ('COLUMN_STEP(r5, r0)', ['SET r0, 2', 'ADD r0, r5']),
])
def test_each_helper_expands_to_its_documented_instructions(use, expansion):
    assert texts('#include <unit.h>\nthere:\nrest:\n' + use) == [
        'there:', 'rest:'] + expansion


def test_a_helper_costs_what_it_replaces():
    written_out = ('SELF\nSUB r3, 3\nJIF neg r3, rest\nFLAG enemy\n'
                   'JIF neg r0, rest\nMOVE south\nHALT\nrest: SLEEP 1')
    with_helpers = ('#include <unit.h>\nUNLESS_AFFORD(3, rest)\nFLAG enemy\n'
                    'IF_NONE(FOUND_X, rest)\nSTEP(south)\nrest: REST')
    plain, helped = Program(written_out), Program(with_helpers)
    assert plain.ticks == helped.ticks
    from board_game_concept.domain.army_map import ArmyMap
    snap = Snapshot(3, 8, 8, 1, {'me': (2, 2)}, {1: (3, 0), 2: (3, 7)},
                    ArmyMap())
    me = {'x': 2, 'y': 2, 'health': 4, 'energy': 10, 'flag': False,
          'number': 0}
    a = run(plain, snap, me, None, {}, [], 5, 10, 0)
    b = run(helped, snap, me, None, {}, [], 5, 10, 0)
    assert (a.order, a.sleep, a.ticks) == (b.order, b.sleep, b.ticks)
    assert a.order == 3


# --- cost and bounds

def test_pricing_a_macro_line():
    program = Program('#include <unit.h>\nUNLESS_AFFORD(2, rest)\nrest: REST')
    assert program.listing() == [
        (1, '#include <unit.h>', None),
        (2, 'UNLESS_AFFORD(2, rest)', 3),
        (3, 'rest: REST', 1)]
    assert program.ticks == 4


def test_a_listing_shows_what_a_macro_line_expands_to():
    program = Program('#define here_x r6\nSELF ; look\nMOV here_x, r0\n'
                      '#include <unit.h>\nSTEP(east)')
    assert program.listing(expanded=True) == [
        (1, '#define here_x r6', None, []),
        (2, 'SELF ; look', 1, []),
        (3, 'MOV here_x, r0', 1, ['MOV r6, r0']),
        (4, '#include <unit.h>', None, []),
        (5, 'STEP(east)', 1, ['MOVE east', 'HALT'])]


def test_an_expansion_that_explodes_is_refused():
    lines = ['#define A0 SELF \\', '    SELF']
    for n in range(1, 21):
        lines.append(f'#define A{n} A{n - 1} \\')
        lines.append(f'    A{n - 1}')
    lines.append('A20')
    with pytest.raises(ProgramError) as refused:
        expand('\n'.join(lines))
    assert refused.value.line == len(lines)
    assert str(MAX_LINES) in str(refused.value)


def test_too_deep_a_nest_is_refused():
    lines = ['#define A0 SELF']
    for n in range(1, MAX_DEPTH + 2):
        lines.append(f'#define A{n} A{n - 1}')
    lines.append(f'A{MAX_DEPTH + 1}')
    with pytest.raises(ProgramError) as refused:
        expand('\n'.join(lines))
    assert refused.value.line == len(lines)


# --- everything speaks of the source line

def test_an_error_inside_a_macro_names_the_line_and_the_macro():
    with pytest.raises(ProgramError) as refused:
        Program('#define STEP_UP MOVE up \\\n    HALT\n' + 'SELF\n' * 9
                + 'STEP_UP')
    assert refused.value.line == 12
    assert 'in STEP_UP' in str(refused.value)
    assert 'MOVE takes' in str(refused.value)


def test_an_unknown_instruction_from_a_macro():
    with pytest.raises(ProgramError) as refused:
        Program('#define THINK PONDER\nSELF\nTHINK')
    assert refused.value.line == 3
    assert 'in THINK' in str(refused.value)


def test_a_bad_directive_is_refused_naming_the_line():
    with pytest.raises(ProgramError) as refused:
        Program('SELF\n#define 3x r0')
    assert refused.value.line == 2


def test_a_halt_inside_a_macro_is_traced_at_the_source_line():
    text = '#define THINK_HARD ' + 'NEAREST enemy \\\n    ' * 30 + 'HALT\n'
    text += 'SELF\n' * 18 + 'THINK_HARD'
    program = Program(text)
    from board_game_concept.domain.army_map import ArmyMap
    snap = Snapshot(3, 8, 8, 1, {'me': (2, 2)}, {}, ArmyMap())
    me = {'x': 2, 'y': 2, 'health': 4, 'energy': 10, 'flag': False,
          'number': 0}
    result = run(program, snap, me, None, {}, [], 1, 10, 0)
    assert result.halted == 50


def test_the_source_is_what_a_type_carries():
    text = '#include <unit.h>\nREST'
    program = Program(text)
    assert program.text == text
    assert [i.op for i in program.instructions] == ['SLEEP']


def test_the_module_reads_no_file(monkeypatch):
    def no_open(*args, **kwargs):
        raise AssertionError('the preprocessor opened a file')
    monkeypatch.setattr(builtins, 'open', no_open)
    assert preprocess.expand('#include <unit.h>\nSTEP(north)')

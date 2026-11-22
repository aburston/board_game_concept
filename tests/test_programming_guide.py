"""The programming guide's examples are programs the machine accepts.

Every fenced block marked `asm` in `PROGRAMMING_GUIDE.md` is run through the
parser, so that an example a reader copies is one that would be accepted,
and the guide cannot drift from the language it describes. A block that is a
fragment - no path to its labels - is still a parse, because what is checked
is the expansion and the instruction set, which is what a copied fragment
has to pass too.
"""

import re
from pathlib import Path

import pytest

from board_game_concept.domain.program import Program

GUIDE = Path(__file__).resolve().parent.parent / 'PROGRAMMING_GUIDE.md'


def asm_blocks():
    text = GUIDE.read_text()
    return re.findall(r'```asm\n(.*?)```', text, re.S)


def test_the_guide_has_asm_examples():
    assert len(asm_blocks()) >= 5


@pytest.mark.parametrize('block', asm_blocks(),
                         ids=lambda block: block.strip().splitlines()[0][:40])
def test_every_asm_example_in_the_guide_is_accepted(block):
    program = Program(block)
    # the unit header on its own defines names and no instruction; every
    # other example is a program or a fragment with instructions in it
    assert program.instructions or block.lstrip().startswith('; unit.h')


def test_the_guide_prints_the_unit_header_as_shipped():
    from board_game_concept.domain.preprocess import UNIT_H
    assert UNIT_H in GUIDE.read_text()

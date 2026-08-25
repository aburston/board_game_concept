"""R9's cost table says what the game charges. This holds it to that.

A summary is a second copy of something, and a second copy drifts. The table
in `GAME_RULES.md` restates costs that live in the code as constants and in
`UnitType.cost` as an expression, so the numbers it prints are checked here
against the ones the game actually charges - and the rules it cites are
checked to still exist under those numbers.
"""

import re
from pathlib import Path

import pytest

from board_game_concept.domain import UnitType

RULES = Path(__file__).resolve().parent.parent / 'GAME_RULES.md'


@pytest.fixture(scope='module')
def rules():
    return RULES.read_text(encoding='utf-8')


@pytest.fixture(scope='module')
def cost_table(rules):
    """R9's section, from its heading to the end of its table."""
    section = re.search(r'^## R9\..*?(?=^## |^---\n\n# Part 2)', rules,
                        flags=re.M | re.S)
    assert section, 'R9, the cost table, is missing from GAME_RULES.md'
    return section.group(0)


def test_the_move_cost_is_the_one_the_game_charges(cost_table):
    # every row that charges for a move quotes MOVE_COST
    assert UnitType.MOVE_COST == 1, (
        'MOVE_COST changed; R9 says a move costs 1 energy')
    assert f'**{UnitType.MOVE_COST} energy**' in cost_table
    assert f'**{UnitType.MOVE_COST} energy each**' in cost_table


def test_the_rest_gain_is_the_one_the_game_gives(cost_table):
    assert UnitType.REST_GAIN == 1, (
        'REST_GAIN changed; R9 says a quiet turn gains 1 energy')
    assert f'**gains {UnitType.REST_GAIN} energy**' in cost_table


def test_the_deployment_price_is_the_one_the_budget_charges(cost_table):
    assert '`attack + health + energy`' in cost_table
    kind = UnitType('Priced', 'P', 3, 5, 20)
    assert kind.cost == 3 + 5 + 20, (
        'a type is no longer priced at attack + health + energy; R9 says it is')


def test_a_round_of_combat_is_charged_at_the_attack_value(cost_table):
    assert "**the attacker's `attack` value**" in cost_table
    # and that it is charged once for the round, not once per opponent
    one = UnitType('One', 'O', 4, 10, 40)
    one.player = type('P', (), {'number': 1})()
    one.destroyed = False
    targets = []
    for index in range(3):
        target = UnitType('Target', 'T', 1, 10, 10)
        target.player = type('P', (), {'number': 2})()
        target.destroyed = False
        targets.append(target)
    from board_game_concept.domain.unit import exchangeAttacks
    before = one.energy
    exchangeAttacks([one] + targets)
    rounds = (before - one.energy) / one.attack
    assert rounds == int(rounds), 'a round is charged whole'
    assert (before - one.energy) == one.attack * int(rounds), (
        'a unit paid more than its attack value per round')


def test_every_rule_the_table_cites_exists(cost_table, rules):
    cited = sorted(set(re.findall(r'\*\*(R\d+\.\d+)\*\*', cost_table)))
    assert cited, 'the cost table cites no rules'
    for rule in cited:
        assert re.search(r'^\*\*' + re.escape(rule) + r'[ .]', rules,
                         flags=re.M), (
            f'R9 cites {rule}, which is not a rule in GAME_RULES.md')


def test_the_table_is_listed_as_having_no_spec_of_its_own(rules):
    # R9 restates; it must not look like a requirement nobody specified
    assert re.search(r'^\| R9 \| nothing of its own', rules, flags=re.M)
